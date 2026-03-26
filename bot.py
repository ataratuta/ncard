import logging
import math
import numpy as np
import matplotlib.pyplot as plt
import sqlite3 as sl
import telebot
from telebot import types
import os
import sys
from dotenv import load_dotenv
import ephem
from openai import OpenAI
import json
import datetime

from telebot.types import ReplyKeyboardRemove

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
client = OpenAI(api_key=os.getenv('API'))

user_data = {}
user_starcharts = {}

con = sl.connect('reports.db')
def conn():
    return sl.connect('reports.db')
with conn():
    data = con.execute("select count(*) from sqlite_master where type='table' and name='users'")
    cursor = con.cursor()
    for row in data:
        if row[0] == 0:
            with con:
                cursor.execute("""
                  CREATE TABLE IF NOT EXISTS users (
                     id VARCHAR(200) PRIMARY KEY,
                     username VARCHAR(200),
                     data VARCHAR(20000),
                     starchart VARCHAR(2000000)
                  );
                """)
def add_user(user_id):
    with conn() as con:
        cursor = con.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (id, username, data) VALUES (?, ?, ?)',
                (user_id, user_data[user_id]['username'], json.dumps(user_data[user_id]))
            )
            logger.info(f"User {user_id} saved to DB")
        except Exception as e:
            logger.error(f"DB error for user {user_id}: {e}")
        con.commit()
def add_starchart(user_id):
    with conn() as con:
        cursor = con.cursor()
        try:
            cursor.execute('UPDATE users SET starchart = ? WHERE id = ?', (json.dumps(user_starcharts[user_id]), user_id))
            logger.info(f"User {user_id} saved to DB")
        except Exception as e:
            logger.error(f"DB error for user {user_id}: {e}")
        con.commit()


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
def draw_natal_chart(chart_data, output_file="natal_chart.png"):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.1)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)
    ax.set_title("Натальная карта", va='bottom', fontsize=16)

    theta = np.linspace(0, 2 * np.pi, 720)
    ax.plot(theta, np.full_like(theta, 1.0), linewidth=2)
    ax.plot(theta, np.full_like(theta, 0.75), linewidth=1)
    ax.plot(theta, np.full_like(theta, 0.45), linewidth=1)

    zodiac_signs = [
        'Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
        'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
    ]

    for i in range(12):
        start_deg = i * 30
        angle = start_deg * math.pi / 180
        ax.plot([angle, angle], [0.75, 1.0], linewidth=1)
        text_angle = (start_deg+15) * math.pi / 180
        ax.text(
            text_angle,
            0.87,
            zodiac_signs[i],
            ha='center',
            va='center',
            fontsize=10
        )
        ax.text(
            angle,
            1.03,
            f"{start_deg}°",
            ha='center',
            va='center',
            fontsize=8
        )

    planet_labels = {
        'Солнце': '☉',
        'Луна': '☽',
        'Меркурий': '☿',
        'Венера': '♀',
        'Марс': '♂',
        'Юпитер': '♃',
        'Сатурн': '♄',
        'Уран': '♅',
        'Нептун': '♆',
        'Плутон': '♇',
    }

    used_angles = []
    for planet, data in chart_data.items():
        deg = data['прямое_восхождение'] % 360
        angle = deg * math.pi / 180
        point_radius = 0.58
        text_radius = 0.48
        for used_deg in used_angles:
            if abs(deg - used_deg) < 8:
                point_radius += 0.05
                text_radius -= 0.05
        used_angles.append(deg)
        ax.scatter([angle], [point_radius], s=50)
        label = planet_labels.get(planet, planet)
        ax.text(
            angle,
            text_radius,
            label,
            ha='center',
            va='center',
            fontsize=13
        )
        ax.text(
            angle,
            0.67,
            f"{planet}\n{deg:.1f}°",
            ha='center',
            va='center',
            fontsize=8
        )
    plt.savefig(output_file, bbox_inches='tight', dpi=200)
    plt.close(fig)


menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile = types.KeyboardButton("📖Профиль")
starchart  = types.KeyboardButton("🌌Рассчитать натальную карту")
personality = types.KeyboardButton("💫Анализ личности")
ask_question = types.KeyboardButton("❔Задать вопрос")
match = types.KeyboardButton("💞Совместимость")
menu.add(profile, starchart, personality, ask_question, match)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_button=types.KeyboardButton("Назад")
change = types.KeyboardButton("Изменить данные")
back.add(back_button, change)

options = types.ReplyKeyboardMarkup(resize_keyboard=True)
name=types.KeyboardButton("Имя")
date=types.KeyboardButton("Дата рождения")
time=types.KeyboardButton("Время рождения")
gmt=types.KeyboardButton("Часовой пояс")
place=types.KeyboardButton("Координаты места рождения")
options.add(name, date, time, gmt, place)

true_false = types.ReplyKeyboardMarkup(resize_keyboard=True)
truebutton = types.KeyboardButton("Да")
falsebutton = types.KeyboardButton("Нет")
true_false.add(truebutton, falsebutton)

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    with conn() as con:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (message.from_user.username or str(message.from_user.id),))
        result = cursor.fetchone()
        if result:
            with conn() as con:
                cursor = con.cursor()
                cursor.execute("SELECT data FROM users WHERE username = ?", (message.from_user.username or str(message.from_user.id),))
                data = cursor.fetchone()
                if data: user_data[user_id] = json.loads(data[0])
            with conn() as con:
                cursor = con.cursor()
                cursor.execute("SELECT starchart FROM users WHERE username = ?", (message.from_user.username or str(message.from_user.id),))
                stchart = cursor.fetchone()
                if stchart: user_starcharts[user_id] = json.loads(stchart[0])
            bot.send_message(message.chat.id, "С возвращением! Что тебя интересует?", reply_markup=menu)
        else:
            def intro(message):
                user_data[user_id] = {}
                user_data[user_id]['username'] = message.from_user.username or str(message.from_user.id)
                bot.send_message(message.chat.id, "Добрый день. Введите имя.", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, ask_name)
            def ask_name(message):
                user_id = message.chat.id
                user_data[user_id]['name']=message.text
                if not user_data[user_id]['name'].isalpha():
                    bot.send_message(message.chat.id, "Имя должно содержать только буквы, введите еще раз")
                    bot.register_next_step_handler(message, ask_name)
                    return
                bot.send_message(message.chat.id, "Введите дату рождения\nФормат гггг:мм:дд", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, ask_date)
            def ask_date(message):
                user_id = message.chat.id
                user_data[user_id]['date'] = message.text
                user_data[user_id]['year']=message.text[0:4]
                user_data[user_id]['month'] = message.text[5:7]
                user_data[user_id]['day'] = message.text[8:]
                try:
                    datetime.datetime.strptime(message.text, "%Y:%m:%d")
                except ValueError:
                    bot.send_message(message.chat.id, "Неверный формат даты, введите еще раз. Используйте гггг:мм:дд")
                    bot.register_next_step_handler(message, ask_date)
                    return
                bot.send_message(message.chat.id, "Введите время рождения\nФормат чч:мм", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, ask_time)
            def ask_time(message):
                user_id = message.chat.id
                user_data[user_id]['time'] = message.text
                user_data[user_id]['hour']=message.text[0:2]
                user_data[user_id]['minute'] = message.text[3:]
                try:
                    datetime.datetime.strptime(message.text, "%H:%M")
                except ValueError:
                    bot.send_message(message.chat.id, "Неверный формат времени, введите еще раз. Используйте чч:мм")
                    bot.register_next_step_handler(message, ask_time)
                    return
                bot.send_message(message.chat.id, "Введите часовой пояс(только n)\nФормат GMT+n", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, ask_timezone)
            def ask_timezone(message):
                    user_id = message.chat.id
                    user_data[user_id]['timezone'] = message.text
                    if not (int(user_data[user_id]['timezone'])>=-11 and int(user_data[user_id]['timezone'])<=12):
                        bot.send_message(message.chat.id, "Часовой пояс не подходит. Вводите только цифру после GMT, например, 3")
                        bot.register_next_step_handler(message, ask_timezone)
                        return
                    bot.send_message(message.chat.id, "Введите координаты места рождения\nФормат:\nшш (с.ш.), дд (в.д.)", reply_markup=types.ReplyKeyboardRemove())
                    bot.register_next_step_handler(message, ask_place)
            def ask_place(message):
                user_id = message.chat.id
                user_data[user_id]['place'] = message.text
                try:
                    lat, lon = map(float, message.text.split(","))
                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        raise ValueError
                except:
                    bot.send_message(message.chat.id, "Неверные координаты, введите еще раз. Формат: 55.75, 37.61")
                    bot.register_next_step_handler(message, ask_place)
                    return
                user_data[user_id]['lat'] = lat
                user_data[user_id]['lon'] = lon
                add_user(user_id)
                info = f"""✅ Данные сохранены:
            
        👤 Имя: {user_data[user_id].get('name', 'Не указано')}
        📅 Дата рождения: {user_data[user_id].get('date', 'Не указано')}
        ⏰ Время рождения: {user_data[user_id].get('time', 'Не указано')}
        🌍 Часовой пояс: {user_data[user_id].get('timezone', 'Не указано')}
        🏙️ Место рождения: {user_data[user_id].get('place', 'Не указано')}
            
            Что тебя интересует?"""

                bot.send_message(message.chat.id, info, reply_markup=menu)
            intro(message)



@bot.message_handler(content_types=['text'])
def text_messages(message):
        logger.info(f"User {message.chat.id} sent: {message.text}")
        if message.text == "📖Профиль":
            user_id = message.chat.id
            if user_id in user_data:
                profile_info = f"""📋 Ваш профиль:

    👤 Имя: {user_data[user_id].get('name', 'Не указано')}
    📅 Дата рождения: {user_data[user_id].get('date', 'Не указано')}
    ⏰ Время рождения: {user_data[user_id].get('time', 'Не указано')}
    🌍 Часовой пояс: {user_data[user_id].get('timezone', 'Не указано')}
    🏙️ Место рождения: {user_data[user_id].get('place', 'Не указано')}"""
                bot.send_message(message.chat.id, profile_info, reply_markup=back)
                def backf(message):
                    logger.info(f"User {message.chat.id} sent: {message.text}")
                    if message.text == "Назад":
                        bot.send_message(message.chat.id, "Что тебя интересует?", reply_markup=menu)
                    elif message.text == "Изменить данные":
                        bot.send_message(message.chat.id, "Что ты хочешь изменить?", reply_markup=options)
                        def update(message):
                            if message.text == "Имя":
                                bot.send_message(message.chat.id, "Введите обновленные данные:",
                                                 reply_markup=types.ReplyKeyboardRemove())
                                def namef(message):
                                    user_data[user_id]['name'] = message.text
                                    if not user_data[user_id]['name'].isalpha():
                                        bot.send_message(message.chat.id,
                                                         "Имя должно содержать только буквы, введите еще раз")
                                        bot.register_next_step_handler(message, namef)
                                        return
                                    with conn() as con:
                                        cursor = con.cursor()
                                        try:
                                            cursor.execute('UPDATE users SET data = ? WHERE id = ?',
                                                           (json.dumps(user_data[user_id]), user_id))
                                            logger.info(f"User {user_id} saved to DB")
                                        except Exception as e:
                                            logger.error(f"DB error for user {user_id}: {e}")

                                        con.commit()
                                    bot.send_message(message.chat.id, "✅ Имя обновлено!", reply_markup=menu)
                                bot.register_next_step_handler(message, namef)
                            if message.text == "Дата рождения":
                                bot.send_message(message.chat.id, "Введите обновленные данные:",
                                                 reply_markup=types.ReplyKeyboardRemove())
                                def datef(message):
                                    user_data[user_id]['date'] = message.text
                                    try:
                                        datetime.datetime.strptime(message.text, "%Y:%m:%d")
                                    except ValueError:
                                        bot.send_message(message.chat.id,
                                                         "Неверный формат даты, введите еще раз. Используйте гггг:мм:дд")
                                        bot.register_next_step_handler(message, datef)
                                        return
                                    user_data[user_id]['year'] = message.text[0:4]
                                    user_data[user_id]['month'] = message.text[5:7]
                                    user_data[user_id]['day'] = message.text[8:]
                                    with conn() as con:
                                        cursor = con.cursor()
                                        try:
                                            cursor.execute('UPDATE users SET data = ? WHERE id = ?',
                                                           (json.dumps(user_data[user_id]), user_id))
                                            logger.info(f"User {user_id} saved to DB")
                                        except Exception as e:
                                            logger.error(f"DB error for user {user_id}: {e}")

                                        con.commit()
                                    bot.send_message(message.chat.id, "✅ Дата рождения обновленф!")
                                    bot.send_message(message.chat.id, "Не забудьте пересчитать свою натальную карту!",
                                                     reply_markup=menu)
                                bot.register_next_step_handler(message, datef)
                            if message.text == "Время рождения":
                                bot.send_message(message.chat.id, "Введите обновленные данные:",
                                                 reply_markup=types.ReplyKeyboardRemove())
                                def timef(message):
                                    user_data[user_id]['time'] = message.text
                                    try:
                                        datetime.datetime.strptime(message.text, "%H:%M")
                                    except ValueError:
                                        bot.send_message(message.chat.id,
                                                         "Неверный формат времени, введите еще раз. Используйте чч:мм")
                                        bot.register_next_step_handler(message, timef)
                                        return
                                    user_data[user_id]['hour'] = message.text[0:2]
                                    user_data[user_id]['minute'] = message.text[3:]
                                    with conn() as con:
                                        cursor = con.cursor()
                                        try:
                                            cursor.execute('UPDATE users SET data = ? WHERE id = ?',
                                                           (json.dumps(user_data[user_id]), user_id))
                                            logger.info(f"User {user_id} saved to DB")
                                        except Exception as e:
                                            logger.error(f"DB error for user {user_id}: {e}")
                                        con.commit()
                                    bot.send_message(message.chat.id, "✅ Время рождения обновлено!")
                                    bot.send_message(message.chat.id, "Не забудьте пересчитать свою натальную карту!",
                                                     reply_markup=menu)
                                bot.register_next_step_handler(message, timef)
                            if message.text == "Часовой пояс":
                                bot.send_message(message.chat.id, "Введите обновленные данные:",
                                                 reply_markup=types.ReplyKeyboardRemove())
                                def timezonef(message):
                                    user_data[user_id]['timezone'] = message.text
                                    if not (int(user_data[user_id]['timezone']) >= -11 and int(
                                            user_data[user_id]['timezone']) <= 12):
                                        bot.send_message(message.chat.id,
                                                         "Часовой пояс не подходит. Вводите только цифру после GMT, например, 3")
                                        bot.register_next_step_handler(message, timezonef)
                                        return
                                    with conn() as con:
                                        cursor = con.cursor()
                                        try:
                                            cursor.execute('UPDATE users SET data = ? WHERE id = ?',
                                                           (json.dumps(user_data[user_id]), user_id))
                                            logger.info(f"User {user_id} saved to DB")
                                        except Exception as e:
                                            logger.error(f"DB error for user {user_id}: {e}")

                                        con.commit()
                                    bot.send_message(message.chat.id, "✅ Часовой пояс обновлено!")
                                    bot.send_message(message.chat.id, "Не забудьте пересчитать свою натальную карту!",
                                                     reply_markup=menu)
                                bot.register_next_step_handler(message, timezonef)
                            if message.text == "Координаты места рождения":
                                bot.send_message(message.chat.id, "Введите обновленные данные:", reply_markup=types.ReplyKeyboardRemove())
                                def placef(message):
                                    user_data[user_id]['place'] = message.text
                                    try:
                                        lat, lon = map(float, message.text.split(","))
                                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                                            raise ValueError
                                    except:
                                        bot.send_message(message.chat.id,
                                                         "Неверные координаты, введите еще раз. Формат: 55.75, 37.61")
                                        bot.register_next_step_handler(message, placef)
                                        return
                                    user_data[user_id]['lat'] = lat
                                    user_data[user_id]['lon'] = lon
                                    with conn() as con:
                                        cursor = con.cursor()
                                        try:
                                            cursor.execute('UPDATE users SET data = ? WHERE id = ?',
                                                           (json.dumps(user_data[user_id]), user_id))
                                            logger.info(f"User {user_id} saved to DB")
                                        except Exception as e:
                                            logger.error(f"DB error for user {user_id}: {e}")

                                        con.commit()
                                    bot.send_message(message.chat.id, "✅ Координаты обновлены!")
                                    bot.send_message(message.chat.id, "Не забудьте пересчитать свою натальную карту!",
                                                     reply_markup=menu)
                                bot.register_next_step_handler(message, placef)

                        bot.register_next_step_handler(message, update)
                bot.register_next_step_handler(message, backf)
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
                bot.send_message(message.chat.id, "⏳ Анализирую...")
                def ai_analysis(message):
                   try:
                        logger.info(f"AI request for user {user_id}")
                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {"role": "system",
                                 "content": f"Ты астролог пользователя. Вот его натальная карта: {user_starcharts[user_id]}"},
                                {"role": "user", "content": "Проанализируй мою личность"}
                            ]
                        )
                        reply = response.choices[0].message.content
                        bot.send_message(message.chat.id, reply, reply_markup=menu)
                   except Exception as e:
                        logger.error(f"AI error for user {user_id}: {e}")

                ai_analysis(message)
        elif message.text == "❔Задать вопрос":
            user_id = message.chat.id
            if user_id not in user_starcharts:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)
            else:
                bot.send_message(message.chat.id, "Что тебя интересует?",
                                 reply_markup=types.ReplyKeyboardRemove())
                def ai_answer(message):
                    bot.send_message(message.chat.id, "⏳ Думаю...")
                    try:
                        logger.info(f"AI request for user {user_id}")
                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {"role": "system",
                                 "content": f"Ты астролог пользователя, вот его натальная карта:{user_starcharts[user_id]} Ответь на его вопрос"},
                                {"role": "user", "content": message.text}
                            ]
                        )
                        reply = response.choices[0].message.contenttypes.ReplyKeyboardRemove()
                        bot.send_message(message.chat.id, reply, reply_markup=menu)
                    except Exception as e:
                        logger.error(f"AI error for user {user_id}: {e}")
                    bot.send_message(message.chat.id, reply, reply_markup=menu)
                bot.register_next_step_handler(message, ai_answer)
        elif message.text == "🌌Рассчитать натальную карту" :
            user_id = message.chat.id
            if user_id in user_data:
                bot.send_message(message.chat.id, "⏳ Рассчитываю...")
                try:
                    star_chart = calculate_chart(user_data[user_id]['year'], user_data[user_id]['month'], user_data[user_id]['day'], user_data[user_id]['hour'], user_data[user_id]['minute'], user_data[user_id]['lat'], user_data[user_id]['lon'])
                    logger.info(f"Chart calculated for user {user_id}")
                except Exception as e:
                    logger.error(f"Chart calculating error: {e}")

                user_starcharts[user_id] = star_chart
                add_starchart(user_id)
                filename = f"natal_chart_{user_id}.png"
                try:
                    draw_natal_chart(star_chart, filename)
                    logger.info(f"Chart image created: {filename}")
                except Exception as e:
                    logger.error(f"Chart drawing error: {e}")
                with open(filename, "rb") as photo:
                    try:
                        bot.send_photo(
                            message.chat.id,
                            photo,
                            caption="🌌 Ваша натальная карта",
                            reply_markup=menu
                        )
                    except Exception as e:
                        logger.error(f"Send photo error: {e}")
                os.remove(filename)
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
                chart_text += format_houses_output(
                    calculate_houses(year=user_data[user_id]['year'], month=user_data[user_id]['month'],
                                     day=user_data[user_id]['day'], hour=user_data[user_id]['hour'],
                                     minute=user_data[user_id]['minute']
                                     , lat=user_data[user_id]['lat'], lon=user_data[user_id]['lon']))
                bot.send_message(message.chat.id, chart_text, reply_markup=menu)
            else:
                bot.send_message(message.chat.id,
                                 "Для расчета натальной карты необходимо заполнить профиль. Нажмите /start для начала.",
                                 reply_markup=menu)
        elif message.text == "💞Совместимость":
            user_id = message.chat.id
            if user_id in user_starcharts:
                bot.send_message(message.chat.id, "С кем вы хотите рассчитать совместимость?\nОтправьте юз", reply_markup=ReplyKeyboardRemove())
                def matchf(message):
                    user_id = message.chat.id
                    username = message.text[1:]
                    with conn() as con:
                        cursor = con.cursor()
                        cursor.execute("SELECT * FROM users WHERE username = ?",
                                       (str(username),))
                        result = cursor.fetchone()
                        if not result:
                            bot.send_message(message.chat.id,
                                             "Этот человек не регистрировался в боте! Попробуйте еще раз",
                                             reply_markup=menu)
                        else:
                            with conn() as con:
                                cursor = con.cursor()
                                cursor.execute("SELECT starchart FROM users WHERE username = ?",
                                               (str(username),))
                                stchart = json.loads(cursor.fetchone()[0])
                                if not stchart:
                                    bot.send_message(message.chat.id,
                                                     "Этот человек не рассчитал натальную карту! Попробуйте еще раз",
                                                     reply_markup=menu)
                                else:
                                    def ai_match():
                                        try:
                                            logger.info(f"AI request for user {user_id}")
                                            response = client.chat.completions.create(
                                                model="gpt-4.1-mini",
                                                messages=[
                                                    {"role": "system",
                                                     "content": f"Ты астролог пользователя @{user_data[user_id]['username']}, вот его натальная карта:{user_starcharts[user_id]}, и натальная карта @{username}:{stchart}. Рассчитай их совместимость(отправь только результаты проверки, чтобы твой ответ можно было целиком отправить пользователю), отправь результат в процентах с расшифровкой"},
                                                ]
                                            )
                                            reply = response.choices[0].message.content
                                            return reply
                                        except Exception as e:
                                            logger.error(f"AI error for user {user_id}: {e}")
                                    res = ai_match()
                                    bot.send_message(message.chat.id,
                                                     res)
                                    bot.send_message(message.chat.id,
                                                     f"Хотите ли вы отправить результаты проверки @{username}?",
                                                     reply_markup=true_false)
                                    def tf(message):
                                        if message.text == "Да":
                                            with conn() as con:
                                                cursor = con.cursor()
                                                cursor.execute("SELECT id FROM users WHERE username = ?",
                                                               (str(username),))
                                                id1 = cursor.fetchone()[0]
                                            bot.send_message(id1,
                                                             f"@{user_data[user_id]['username']} рассчитал совместимость с вами:")
                                            bot.send_message(id1,
                                                             res)
                                            bot.send_message(message.chat.id,
                                                             "Отправили, что еще тебя интересует?",
                                                             reply_markup=menu)
                                    bot.register_next_step_handler(message, tf)

                bot.register_next_step_handler(message, matchf)
            else:
                bot.send_message(message.chat.id,
                                 "Натальная карта не создана. Нажмите *🌌Рассчитать натальную карту* для создания",
                                 reply_markup=menu)


con.close()
bot.infinity_polling(timeout=60)
