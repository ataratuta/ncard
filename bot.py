import logging
import telebot
from telebot import types
import os
import sys
from dotenv import load_dotenv
import ephem
import datetime


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


def calculate_chart(year, month, day, hour, minute, lat, lon):
    observer = ephem.Observer()
    observer.lat = lat
    observer.lon = lon
    observer.date = f'{year}/{month}/{day} {hour}:{minute}:00'
    celestial_bodies = {
        'Солнце': ephem.Sun(observer),
        'Луна': ephem.Moon(observer),
        'Меркурий': ephem.Mercury(observer),
        'Венера': ephem.Venus(observer),
        'Марс': ephem.Mars(observer),
        'Юпитер': ephem.Jupiter(observer),
        'Сатурн': ephem.Saturn(observer),
        'Уран': ephem.Uranus(observer),
        'Нептун': ephem.Neptune(observer),
        'Плутон': ephem.Pluto(observer),
    }
    chart_data = {}
    for name, body in celestial_bodies.items():
        constellation = ephem.constellation(body)
        ra_deg = float(body.ra) * 180 / ephem.pi
        dec_deg = float(body.dec) * 180 / ephem.pi

        chart_data[name] = {
            'созвездие': constellation,
            'прямое_восхождение': round(ra_deg, 2),
            'склонение': round(dec_deg, 2),
            'знак_зодиака': zodiac_sign(ra_deg),
        }

    return chart_data
def zodiac_sign(ra_degrees):
    signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    degrees = ra_degrees % 360
    sign_index = int(degrees / 30)
    return signs[sign_index]
def calculate_houses(year, month, day, hour, minute, lat, lon):
    observer = ephem.Observer()
    observer.lat = lat
    observer.lon = lon
    observer.date = f'{year}/{month}/{day} {hour}:{minute}:00'
    houses = []
    for i in range(12):
        house_cusp = ephem.degrees(ephem.degrees(observer.sidereal_time()) + i * 30 * ephem.degree)
        houses.append(house_cusp)
    return houses


menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile = types.KeyboardButton("📖Профиль")
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
    bot.send_message(message.chat.id, "Введите дату рождения\nФормат гггг:мм:дд", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_date)
def ask_date(message):
    user_id = message.chat.id
    user_data[user_id]['date'] = message.text
    user_data[user_id]['year']=message.text[0:4]
    user_data[user_id]['month'] = message.text[5:7]
    user_data[user_id]['day'] = message.text[8:]
    bot.send_message(message.chat.id, "Введите время рождения\nФормат чч:мм", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_time)
def ask_time(message):
    user_id = message.chat.id
    user_data[user_id]['time'] = message.text
    user_data[user_id]['hour']=message.text[0:2]
    user_data[user_id]['minute'] = message.text[3:]
    bot.send_message(message.chat.id, "Введите часовой пояс\nФормат GMT+n", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_timezone)
def ask_timezone(message):
        user_id = message.chat.id
        user_data[user_id]['timezone'] = message.text
        bot.send_message(message.chat.id, "Введите координаты места рождения\nФормат шш.шшшш, дд.дддд", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, ask_place)
def ask_place(message):
    user_id = message.chat.id
    user_data[user_id]['place'] = message.text
    user_data[user_id]['lat'] = message.text[0:7]
    user_data[user_id]['lon'] = message.text[9:]
    info = f"""✅ Данные сохранены:

👤 Имя: {user_data[user_id].get('name', 'Не указано')}
📅 Дата рождения: {user_data[user_id].get('date', 'Не указано')}
⏰ Время рождения: {user_data[user_id].get('time', 'Не указано')}
🌍 Часовой пояс: {user_data[user_id].get('timezone', 'Не указано')}
🏙️ Место рождения: {user_data[user_id].get('place', 'Не указано')}

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
    🏙️ Место рождения: {user_data[user_id].get('place', 'Не указано')}"""
                bot.send_message(message.chat.id, profile_info, reply_markup=menu)
            else:
                bot.send_message(message.chat.id,
                                 "Профиль не заполнен. Нажмите /start для начала.",
                                 reply_markup=menu)
        elif message.text == "🪐Аспекты планет" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
        elif message.text == "🏠Дома в знаках" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
            else:
                answer = "🌌 Ваша дома:\n\n"
                star_chart = user_starcharts[message.chat.id]
                for planet, data in star_chart.items():
                    answer += f"✨ {planet}:\n"
                    answer += f"   Знак: {data['знак_зодиака']}\n"
                bot.send_message(message.chat.id, answer, reply_markup=menu)
        elif message.text == "💫Анализ личности" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
        elif message.text == "❔Задать вопрос" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
            else:
                bot.send_message(message.chat.id, "Что тебя интересует?",
                                 reply_markup=types.ReplyKeyboardRemove())
        elif message.text == "🌌Рассчитать натальную карту" :
            user_id = message.chat.id
            if user_id in user_data:
                star_chart = calculate_chart(user_data[user_id]['year'], user_data[user_id]['month'], user_data[user_id]['day'], user_data[user_id]['hour'], user_data[user_id]['minute'], user_data[user_id]['lat'], user_data[user_id]['lon'])
                chart_text = "🌌 Ваша натальная карта:\n\n"
                for planet, data in star_chart.items():
                    chart_text += f"✨ {planet}:\n"
                    chart_text += f"   Знак: {data['знак_зодиака']}\n"
                    chart_text += f"   Созвездие: {data['созвездие'][0]} ({data['созвездие'][1]})\n"
                    chart_text += f"   Координаты: {data['прямое_восхождение']}°, {data['склонение']}°\n\n"
                user_starcharts[user_id]=star_chart
                bot.send_message(message.chat.id, chart_text, reply_markup=menu)
            else:
                bot.send_message(message.chat.id,
                                 "Для расчета натальной карты необходимо заполнить профиль. Нажмите /start для начала.",
                                 reply_markup=menu)


bot.infinity_polling()