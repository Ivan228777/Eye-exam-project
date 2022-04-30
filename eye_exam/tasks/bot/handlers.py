import telebot
import numpy as np
import cv2 as cv
import sys
import requests
sys.path.insert(1, './openCV/EyeOpenCV/')
from openCV.EyeOpenCV import omr

from bot_settings import API_TOKEN

bot = telebot.TeleBot(API_TOKEN)

BASE_URL = "http://127.0.0.1:8000"


@bot.message_handler(commands=['start'])
def start_command(message):
   bot.send_message(
       message.chat.id,
       'Добро пожаловать!\n' +
       'Отправьте мне фотографии бланков учеников и я их проверю!\n' +
	   'Чтобы увидеть инструкцию, каким образом необходимо делать фотографии  напишите /help\n'
   )
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
		message.chat.id,
		'Во время фотографии телефон необходимо держать параллельно бланку ответов\n' +
		'Не рекоммендуется использовать вспышку\n' +
		'Не желательно делать фотографию при плохом освещении или отбрасывать на бланк ответов тень\n'
	)

@bot.message_handler(content_types=['text'])
def first_message(message):
    if message.text != '/start' or message.text != '/help':
        bot.send_message(message.chat.id, 'Пожалуйста, напишите /help для получения подробной информации о верном способе фотографии или же отправьте саму фотографию.')

@bot.message_handler(content_types=['photo'])

def get_photo(message):
	try:
		photo = message.photo
		file_id = photo[-1].file_id
		file = bot.get_file(file_id)
		downloaded_file = bot.download_file(file.file_path)
		img = np.asarray(bytearray(downloaded_file), dtype="uint8")
		data = omr.get_student_data(omr.find_document(cv.imdecode(img, cv.IMREAD_COLOR)))
		request = requests.post(f'{BASE_URL}/tasks/check',
								data)
		response = request.json()
		bot.send_message(message.chat.id,
						 response['student'] + ": " + str(response['score']) + '/' + (str(response['max_score'])))
	except:
		bot.send_message(message.chat.id, 'Возникла ошибка при проверке фотографии')

bot.polling(none_stop=True)





