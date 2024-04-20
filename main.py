from youtube_search import YoutubeSearch
import telebot
import os
from pytube import YouTube
import random
import string
from datetime import datetime
from telebot import types
import json
import shutil

global global_message

global_message = None

# Установка токена вашего бота
bot_token = 'YOUR_TOKEN_IS_HERE'
bot = telebot.TeleBot(bot_token)


def generate_random_string(length):
    # Создаем строку, содержащую буквы и цифры
    characters = string.ascii_letters + string.digits
    # Генерируем случайную строку заданной длины
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def time_to_seconds(time_str):
    # Проверяем, есть ли в строке информация о часах
    if time_str.count(':') == 2:
        time_format = "%H:%M:%S"
    else:
        time_format = "%M:%S"

    # Парсим строку времени в объект datetime
    time_obj = datetime.strptime(time_str, time_format)

    # Получаем общее количество секунд
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_seconds


def download_audio(url, file_name):
    try:
        folder_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(folder_path)
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_stream.download(filename=file_name)
        return True, None
    except Exception as e:
        return False, str(e)


def search_to_url(message, much):
    request = message.text  # Получаем текст сообщения пользователя
    results = YoutubeSearch(request, max_results=much).to_dict()
    for i in range(much):
        new_result = results[i]
        return [new_result['title'], "https://www.youtube.com/" + new_result['url_suffix'], new_result['duration'],
                new_result['url_suffix']]


def download_send_name(message):
    chat_id = message.chat.id
    global_message = message.text + '.mp3'
    try:

        massive = search_to_url(message, 1)
        if time_to_seconds(massive[2]) > 600:
            raise MemoryError("Слишком длинное, не смогу скачать")
        bot.reply_to(message, massive[0])

        # создаем имя
        code_name = massive[3]
        file = open('data.json', 'r+')

        song_list = json.load(file)

        if code_name in song_list:
            file_name = song_list[code_name] + '.mp3'
            file = open(file_name, 'rb')
            shutil.copy(file.name, global_message)
            bot.send_document(chat_id, open(global_message, 'rb'))
            file.close()
            os.remove(global_message)

        else:
            new_name = generate_random_string(7)
            song_list[code_name] = new_name
            file.seek(0)
            json.dump(song_list, file, indent=4)
            file.truncate()
            file.close()

            success, error = download_audio(massive[1], new_name + '.mp3')

            if success:
                file_name = new_name + '.mp3'
                file = open(file_name, 'rb')
                shutil.copy(file.name, global_message)
                bot.send_document(chat_id, open(global_message, 'rb'))
                file.close()
                os.remove(global_message)

            else:
                bot.reply_to(message, f"Произошла ошибка при загрузке аудио: {error}")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if len(message.text) > 5 and all(char not in message.text for char in ['/', ':', '*', '?', '"', '|', '\\']):
        keyboard = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="Скачать песню", callback_data="search", callback_game=True)
        button.resize_keyboard = True
        keyboard.add(button)
        bot.send_message(message.chat.id, message.text, reply_markup=keyboard)
    else:
        bot.reply_to(message, 'Мы не сможем найти такую песню: слишком короткая или запрещенные символы')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    keyboard = types.ReplyKeyboardRemove()
    message = call.message
    if call.data == "search":
        print(message.text)
        download_send_name(message)


bot.polling()
