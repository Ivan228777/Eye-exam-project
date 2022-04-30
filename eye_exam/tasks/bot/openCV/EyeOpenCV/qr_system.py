import qrcode
from PIL.Image import Image
from workdata import WorkData
import cv2 as cv


def detect_qr_code(image):
    qr_decoder = cv.QRCodeDetector()
    data = qr_decoder.detectAndDecode(image)[0]
    if not data:
        return
    wd = WorkData(int(data[:5]), int(data[5:]))
    return wd


def create_qr_code(id_test: str, id_student: str, qr_size):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    data = f'{(5 - len(id_test)) * "0"}{id_test}{(5 - len(id_student)) * "0"}{id_student}'
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = Image.resize(img, qr_size)
    return img
