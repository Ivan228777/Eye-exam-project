import cv2 as cv
from qr_system import detect_qr_code
import numpy as np
import jsonpickle

CORNER_PATH = './corner.png'
PAPER_FORMAT = (1050, 1485)
DEBUG = False


class OmrException(Exception):
    pass


def debug_window(title, image):
    global DEBUG
    if DEBUG:
        cv.imshow(title, image)
        cv.waitKey(0)


def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")
    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    # return the ordered coordinates
    return rect


def rescale_frame(frame, scale=0.5):
    width = frame.shape[1] * scale
    height = frame.shape[0] * scale
    dimensions = int(width), int(height)
    return cv.resize(frame, dimensions, interpolation=cv.INTER_AREA)


def rescale_frame_size(frame, size=PAPER_FORMAT):
    return cv.resize(frame, size, interpolation=cv.INTER_AREA)


def normalize(im):
    """Converts `im` to black and white.
    Applying a threshold to a grayscale image will make every pixel either
    fully black or fully white. Before doing so, a common technique is to
    get rid of noise (or super high frequency color change) by blurring the
    grayscale image with a Gaussian filter."""
    im_gray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)

    # Filter the grayscale image with a 3x3 kernel
    blurred = cv.GaussianBlur(im_gray, (3, 3), 0)

    # Applies a Gaussian adaptive thresholding. In practice, adaptive thresholding
    # seems to work better than appling a single, global threshold to the image.
    # This is particularly important if there could be shadows or non-uniform
    # lighting on the answer sheet. In those scenarios, using a global thresholding
    # technique might yield paricularly bad results.
    # The choice of the parameters blockSize = 77 and C = 10 is as much as an art
    # as a science and domain-dependand.
    # In practice, you might want to try different  values for your specific answer
    # sheet.
    return cv.adaptiveThreshold(
        blurred, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 77, 10)


def get_approx_contour(contour, tol=.01):
    """Gets rid of 'useless' points in the contour."""
    epsilon = tol * cv.arcLength(contour, True)
    return cv.approxPolyDP(contour, epsilon, True)


def get_contours(image_gray):
    contours, _ = cv.findContours(
        image_gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    return map(get_approx_contour, contours)


def calculate_contour_features(contour):
    """Calculates interesting properties (features) of a contour.
    We use these features to match shapes (contours). In this script,
    we are interested in finding shapes in our input image that look like
    a corner. We do that by calculating the features for many contours
    in the input image and comparing these to the features of the corner
    contour. By design, we know exactly what the features of the real corner
    contour look like - check out the calculate_corner_features function.
    It is crucial for these features to be invariant both to scale and rotation.
    In other words, we know that a corner is a corner regardless of its size
    or rotation. In the past, this script implemented its own features, but
    OpenCV offers much more robust scale and rotational invariant features
    out of the box - the Hu moments.
    """
    moments = cv.moments(contour)
    return cv.HuMoments(moments)


def calculate_corner_features(path=CORNER_PATH):
    """Calculates the array of features for the corner contour.
    In practice, this can be pre-calculated, as the corners are constant
    and independent from the inputs.
    We load the img/corner.png file, which contains a single corner, so we
    can reliably extract its features. We will use these features to look for
    contours in our input image that look like a corner.
    """
    corner_img = cv.imread(path)
    corner_img_gray = cv.cvtColor(corner_img, cv.COLOR_BGR2GRAY)
    contours, hierarchy = cv.findContours(
        corner_img_gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # We expect to see only two contours:
    # - The "outer" contour, which wraps the whole image, at hierarchy level 0
    # - The corner contour, which we are looking for, at hierarchy level 1
    # If in trouble, one way to check what's happening is to draw the found contours
    # with cv2.drawContours(corner_img, contours, -1, (255, 0, 0)) and try and find
    # the correct corner contour by drawing one contour at a time. Ideally, this
    # would not be done at runtime.
    if len(contours) != 2:
        raise RuntimeError(
            'Did not find the expected contours when looking for the corner')

    # Following our assumptions as stated above, we take the contour that has a parent
    # contour (that is, it is _not_ the outer contour) to be the corner contour.
    # If in trouble, verify that this contour is the corner contour with
    # cv2.drawContours(corner_img, [corner_contour], -1, (255, 0, 0))
    corner_contour = next(ct
                          for i, ct in enumerate(contours)
                          if hierarchy[0][i][3] != -1)

    return calculate_contour_features(corner_contour)


def features_distance(f1, f2):
    return np.linalg.norm(np.array(f1) - np.array(f2))


def get_corners(contours, path=CORNER_PATH, n=4):
    """Returns the 4 contours that look like a corner the most.
    In the real world, we cannot assume that the corners will always be present,
    and we likely need to decide how good is good enough for contour to
    look like a corner.
    This is essentially a classification problem. A good approach would be
    to train a statistical classifier model and apply it here. In our little
    exercise, we assume the corners are necessarily there."""
    #corner_features = calculate_corner_features(path)
    corner_features = CORNER_FEATURES
    return sorted(
        contours,
        key=lambda c: features_distance(
            corner_features,
            calculate_contour_features(c)))[:n]


def perspective_transform(img, points):
    """Applies a 4-point perspective transformation in `img` so that `points`
    are the new corners."""
    source = np.array(
        points,
        dtype="float32")

    source = order_points(source)
    widthA = np.sqrt(((source[2][0] - source[3][0]) ** 2) + ((source[2][1] - source[2][1]) ** 2))
    widthB = np.sqrt(((source[1][0] - source[0][0]) ** 2) + ((source[1][1] - source[0][1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((source[1][0] - source[2][0]) ** 2) + ((source[1][1] - source[2][1]) ** 2))
    heightB = np.sqrt(((source[0][0] - source[3][0]) ** 2) + ((source[0][1] - source[3][1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dest = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]],
        dtype="float32")

    transf = cv.getPerspectiveTransform(source, dest)
    warped = cv.warpPerspective(img, transf, (maxWidth, maxHeight))
    return warped


def get_4points(b_rect):
    points = list()
    points.append([b_rect[0], b_rect[1]])
    points.append([b_rect[0] + b_rect[2], b_rect[1]])
    points.append([b_rect[0] + b_rect[2], b_rect[1] + b_rect[3]])
    points.append([b_rect[0], b_rect[1] + b_rect[3]])
    return np.array(points)


def get_question_data(q_image):
    q_image = q_image[q_image.shape[0] // 2 - 5:q_image.shape[0] - 8, 5:q_image.shape[1] - 10]
    im_normalized = cv.threshold(cv.cvtColor(q_image, cv.COLOR_BGR2GRAY), 120, 255, cv.THRESH_BINARY_INV)[1]
    im_canny = cv.Canny(im_normalized, 100, 300, 3)
    debug_window('Canny question', im_normalized)
    contours, hierarchy = cv.findContours(im_canny, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    answers = []
    for ind, cont in enumerate(contours):
        sm = cv.arcLength(cont, True)
        apd = cv.approxPolyDP(cont, 0.02 * sm, True)
        if len(apd) > 6:
            answers.append(cont)
    answers.sort(key=lambda x: x[0][0][0])
    box_images = []
    for i in answers:
        # box = cv.boxPoints(cv.minAreaRect(i))
        box = get_4points(cv.boundingRect(i))
        # box = np.intp(box)
        if DEBUG:
            cv.drawContours(q_image, [box], -1, (255, 255, 0), 3)
        box_im = perspective_transform(im_normalized, box)
        debug_window('Answer in Box', box_im)
        box_images.append(box_im)
    debug_window('Question', q_image)
    if not box_images:
        raise OmrException('Empty answer box')
    d = max(enumerate(box_images), key=lambda x: cv.countNonZero(x[1]))
    return d[0]


def find_question(image):
    image = image[image.shape[0] // 6:image.shape[0] - 20, 20:image.shape[1] - 20]
    im_normalized = cv.Canny(image, 100, 300, 3)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (8, 8))
    closed = cv.morphologyEx(im_normalized, cv.MORPH_CLOSE, kernel)
    contours, hierarchy = cv.findContours(closed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    debug_window('Canny questions', rescale_frame(closed, 0.5))
    box = []
    for ind, cont in enumerate(contours):
        sm = cv.arcLength(cont, True)
        apd = cv.approxPolyDP(cont, 0.02 * sm, True)
        if len(apd) == 4:
            box.append(cont)
            if DEBUG:
                cv.drawContours(image, [cont], -1, (255, 0, 0), 5)
    #  box.sort(key=cv.contourArea, reverse=True)
    debug_window('Questions', rescale_frame(image))
    if not box:
        raise OmrException("No question-box")
    box.sort(key=lambda x: x[0][0][1])
    answers = {}
    for ind, cont in enumerate(box):
        sm = cv.arcLength(cont, True)
        apd = cv.approxPolyDP(cont, 0.02 * sm, True)
        question = perspective_transform(image, np.concatenate(apd))
        question_data = get_question_data(question)
        answers[ind] = question_data
    return answers


def find_document(image):
    blur = cv.blur(image, (3, 3))
    im_normalized = normalize(blur)
    debug_window('Normalized image', rescale_frame(im_normalized, 0.5))
    contours = get_contours(im_normalized)
    corners = get_corners(contours)
    all_points = cv.convexHull(np.concatenate(corners))
    point1 = sorted(all_points, key=lambda x: x[0][0] + x[0][1], reverse=True)[0]
    point2 = sorted(all_points, key=lambda x: x[0][1] - x[0][0], reverse=True)[0]
    point3 = sorted(all_points, key=lambda x: x[0][0] + x[0][1])[0]
    point4 = sorted(all_points, key=lambda x: x[0][0] - x[0][1], reverse=True)[0]
    points = np.concatenate([point1, point2, point3, point4])
    image = perspective_transform(image, points)
    image = rescale_frame_size(image)
    debug_window('Scan', rescale_frame(image, 0.5))
    return image


def get_student_data(image):
    im = image[0:image.shape[0] // 6, image.shape[1] // 6 * 4:image.shape[1]]
    data = qrs.detect_qr_code(im)
    if data is None:
        raise OmrException('Empty QR-Code')
    answ = find_question(image)
    data.student_answers = answ
    json_data = jsonpickle.encode(data, unpicklable=False)
    return json_data


CORNER_FEATURES = calculate_corner_features(CORNER_PATH)
