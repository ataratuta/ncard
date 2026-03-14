import logging
import math

import telebot
from telebot import types
import os
import sys
from dotenv import load_dotenv
import ephem
import datetime
import openai
from openai import OpenAI


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



API = os.getenv('API')
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=API)

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
    planets_positions = {}
    chart_data = {}
    angles = calculate_angles(observer, planets_positions)
    houses = calculate_houses(year, month, day, hour, minute, lat, lon)
    for name, body in celestial_bodies.items():
        constellation = ephem.constellation(body)
        ra_deg = float(body.ra) * 180 / ephem.pi
        dec_deg = float(body.dec) * 180 / ephem.pi
        planets_positions[name] = ra_deg
        chart_data[name] = {
            'созвездие': constellation,
            'прямое_восхождение': round(ra_deg, 2),
            'склонение': round(dec_deg, 2),
            'знак_зодиака': zodiac_sign(ra_deg),
            'углы': angles,
            'дома': houses,
        }
    return chart_data
def zodiac_sign(ra_degrees):
    signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    degrees = ra_degrees % 360
    sign_index = int(degrees / 30)
    return signs[sign_index]


def calculate_houses(year, month, day, hour, minute, lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = f'{year}/{month}/{day} {hour}:{minute}:00'
    sidereal_time = observer.sidereal_time()
    st_degrees = float(sidereal_time) * 15
    houses = []
    for i in range(12):
        house_cusp_deg = (st_degrees + i * 30) % 360
        house_cusp = ephem.degrees(str(house_cusp_deg))
        houses.append(house_cusp)
    return houses
def format_houses_output(houses_cusps):
    house_names = {
        1: "I (Асцендент)",
        2: "II",
        3: "III",
        4: "IV (IC)",
        5: "V",
        6: "VI",
        7: "VII (Десцендент)",
        8: "VIII",
        9: "IX",
        10: "X (MC)",
        11: "XI",
        12: "XII"
    }
    zodiac_signs = [
        'Овен', 'Телец', 'Близнецы', 'Рак',
        'Лев', 'Дева', 'Весы', 'Скорпион',
        'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
    ]
    output = "🏠 *КУСПИДЫ ДОМОВ*\n\n"
    for i, cusp in enumerate(houses_cusps, 1):
        degrees = float(cusp) * 180 / math.pi
        norm_degrees = degrees % 360
        sign_index = int(norm_degrees / 30)
        sign = zodiac_signs[sign_index]
        sign_degree = norm_degrees % 30
        emoji = {
            1: "⬆️", 4: "⬇️", 7: "⬇️", 10: "⬆️"
        }.get(i, "•")
        output += f"{emoji} *{house_names[i]}:* "
        output += f"{sign} {int(sign_degree)}°\n"
        if i in [1, 4, 7, 10]:
            output += "   ⚡ Угловой дом\n"
        if i == 1:
            output += "   *Значение:* Личность, внешность, начало жизни\n"
        elif i == 4:
            output += "   *Значение:* Семья, дом, корни, прошлое\n"
        elif i == 7:
            output += "   *Значение:* Партнерство, брак, отношения\n"
        elif i == 10:
            output += "   *Значение:* Карьера, цели, статус\n"
    return output

def calculate_angles(observer, planets_positions):
    sidereal_time = observer.sidereal_time()
    asc_ra = float(sidereal_time) * 15
    asc = asc_ra % 360
    asc_sign = zodiac_sign(asc)
    asc_degree = round(asc % 30, 2)
    mc = (asc + 90) % 360
    mc_sign = zodiac_sign(mc)
    mc_degree = round(mc % 30, 2)
    dsc = (asc + 180) % 360
    dsc_sign = zodiac_sign(dsc)
    ic = (mc + 180) % 360
    ic_sign = zodiac_sign(ic)
    return {
        'ascendant': {
            'знак': asc_sign,
            'градус': round(asc_degree, 2),
            'координата': round(asc, 2)
        },
        'midheaven': {
            'знак': mc_sign,
            'градус': round(mc_degree, 2),
            'координата': round(mc, 2)
        },
        'descendant': {
            'знак': dsc_sign,
            'координата': round(dsc, 2)
        },
        'imum_coeli': {
            'знак': ic_sign,
            'координата': round(ic, 2)
        }
    }


menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile = types.KeyboardButton("📖Профиль")
starchart  = types.KeyboardButton("🌌Рассчитать натальную карту")
personality = types.KeyboardButton("💫Анализ личности")
ask_question = types.KeyboardButton("❔Задать вопрос")
menu.add(profile, starchart, personality, ask_question)

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
        bot.send_message(message.chat.id, "Введите координаты места рождения\nФормат шш (с.ш.), дд (в.д.)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, ask_place)
def ask_place(message):
    user_id = message.chat.id
    user_data[user_id]['place'] = message.text
    user_data[user_id]['lat'] = message.text[0:2]
    user_data[user_id]['lon'] = message.text[5:]
    """add_user(user_id, message.from_user.username)"""
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
        elif message.text == "💫Анализ личности" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
            else:
                def ai_analysis(message):
                   response = client.chat.completions.create(
                   model="gpt-5-mini",
                       messages=[
                           {"role": "system",
                            "content": f"Ты астролог. Вот натальная карта: {user_starcharts[user_id]}"},
                           {"role": "user", "content": "Проанализируй мою личность"}
                       ]

                   )
                   reply = response["choices"][0]["message"]["content"]
                   bot.send_message(message.chat.id, reply, reply_markup=menu)

                ai_analysis(message)
        elif message.text == "❔Задать вопрос" :
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
            else:
                bot.send_message(message.chat.id, "Что тебя интересует?",
                                 reply_markup=types.ReplyKeyboardRemove())
                def ai_answer(message):
                   response = client.chat.completions.create(
                   model="gpt-5-mini",
                   messages=[
                    {"role": "system", "content": f"Ты таролог пользователя, вот его натальная карта:{user_starcharts[user_id]} Ответь на его вопрос"},
                    {"role": "user", "content": message.text}
                   ]
                   )
                   reply = response["choices"][0]["message"]["content"]
                   bot.send_message(message.chat.id, reply, reply_markup=menu)
                bot.register_next_step_handler(message, ai_answer)
        elif message.text == "🌌Рассчитать натальную карту" :
            user_id = message.chat.id
            if user_id in user_data:
                star_chart = calculate_chart(user_data[user_id]['year'], user_data[user_id]['month'], user_data[user_id]['day'], user_data[user_id]['hour'], user_data[user_id]['minute'], user_data[user_id]['lat'], user_data[user_id]['lon'])
                user_starcharts[user_id] = star_chart
                """add_starchart(user_id, message.from_user.username)"""
                chart_text = "🌌 Ваша натальная карта:\n\n"
                for planet, data in star_chart.items():
                    chart_text += f"✨ {planet}:\n"
                    chart_text += f"   Знак: {data['знак_зодиака']}\n"
                    chart_text += f"   Созвездие: {data['созвездие'][1]}\n"
                    chart_text += f"   Координаты: {data['прямое_восхождение']}°, {data['склонение']}°\n\n"
                chart_text += "⚡ УГЛЫ КАРТЫ:\n"
                chart_text += f"   ASC: {data['углы']['ascendant']['знак']} {data['углы']['ascendant']['градус']}°\n"
                chart_text += f"   MC:  {data['углы']['midheaven']['знак']} {data['углы']['midheaven']['градус']}°\n"
                chart_text += f"   DSC: {data['углы']['descendant']['знак']}\n"
                chart_text += f"   IC:  {data['углы']['imum_coeli']['знак']}\n\n"
                chart_text += format_houses_output(calculate_houses(year=user_data[user_id]['year'], month=user_data[user_id]['month'], day=user_data[user_id]['day'], hour=user_data[user_id]['hour'], minute=user_data[user_id]['minute']
                                                                , lat=user_data[user_id]['lat'], lon=user_data[user_id]['lon']))
                bot.send_message(message.chat.id, chart_text, reply_markup=menu)
            else:
                bot.send_message(message.chat.id,
                                 "Для расчета натальной карты необходимо заполнить профиль. Нажмите /start для начала.",
                                 reply_markup=menu)


bot.infinity_polling()