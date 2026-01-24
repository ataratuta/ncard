import logging
import telebot
from telebot import types
import os
import sys
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

telebot.logger.setLevel(logging.INFO)


def init_datebase():
    pass

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

user_data = {}
user_starcharts = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile=types.KeyboardButton("📖Профиль")
starchart  = types.KeyboardButton("🌌Рассчитать натальную карту")
planets = types.KeyboardButton("🪐Аспекты планет")
houses = types.KeyboardButton("🏠Дома в знаках")
personality = types.KeyboardButton("💫Анализ личности")
ask_question = types.KeyboardButton("❔Задать вопрос")
menu.add(profile, starchart, planets, houses, personality, ask_question)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_button=types.KeyboardButton("Назад")
back.add(back_button)


@bot.message_handler(commands=['start'])
def start_message(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Добрый день. Введите имя.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_name)
def ask_name(message):
    user_id = message.chat.id
    user_data[user_id]['name']=message.text
    bot.send_message(message.chat.id, "Введите дату рождения\nФормат дд:мм:гггг", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_date)
def ask_date(message):
    user_id = message.chat.id
    user_data[user_id]['date']=message.text
    bot.send_message(message.chat.id, "Введите время рождения\nФормат чч:мм", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_time)
def ask_time(message):
    user_id = message.chat.id
    user_data[user_id]['time']=message.text
    bot.send_message(message.chat.id, "Введите часовой пояс\nФормат GMT+n", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_timezone)
def ask_timezone(message):
        user_id = message.chat.id
        user_data[user_id]['timezone'] = message.text
        bot.send_message(message.chat.id, "Введите город рождения\nФормат страна, город", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, ask_city)
def ask_city(message):
    user_id = message.chat.id
    user_data[user_id]['city'] = message.text
    info = f"""✅ Данные сохранены:

👤 Имя: {user_data[user_id].get('name', 'Не указано')}
📅 Дата рождения: {user_data[user_id].get('date', 'Не указано')}
⏰ Время рождения: {user_data[user_id].get('time', 'Не указано')}
🌍 Часовой пояс: {user_data[user_id].get('timezone', 'Не указано')}
🏙️ Город рождения: {user_data[user_id].get('city', 'Не указано')}

    Что тебя интересует?"""

    bot.send_message(message.chat.id, info, reply_markup=menu)



@bot.message_handler(content_types=['text'])
def text_messages(message):
        if message.text == "Назад":
            bot.send_message(message.chat.id, "Что тебя интересует?", reply_markup=menu)
        elif message.text == "📖Профиль":
            user_id = message.chat.id
            if user_id in user_data:
                profile_info = f"""📋 Ваш профиль:

    👤 Имя: {user_data[user_id].get('name', 'Не указано')}
    📅 Дата рождения: {user_data[user_id].get('date', 'Не указано')}
    ⏰ Время рождения: {user_data[user_id].get('time', 'Не указано')}
    🌍 Часовой пояс: {user_data[user_id].get('timezone', 'Не указано')}
    🏙️ Город рождения: {user_data[user_id].get('city', 'Не указано')}"""
                bot.send_message(message.chat.id, profile_info, reply_markup=menu)
            else:
                bot.send_message(message.chat.id,
                                 "Профиль не заполнен. Нажмите /start для начала.",
                                 reply_markup=menu)
        elif message.text == "🪐Аспекты планет" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите 🌌Рассчитать натальную карту для создания",
                                 reply_markup=menu)
        elif message.text == "🏠Дома в знаках" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите 🌌Рассчитать натальную карту для создания",
                                 reply_markup=menu)
        elif message.text == "💫Анализ личности" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите 🌌Рассчитать натальную карту для создания",
                                 reply_markup=menu)
        elif message.text == "❔Задать вопрос" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите 🌌Рассчитать натальную карту для создания",
                                 reply_markup=menu)
            else:
                bot.send_message(message.chat.id, "Что тебя интересует?",
                                 reply_markup=types.ReplyKeyboardRemove())


bot.infinity_polling()



