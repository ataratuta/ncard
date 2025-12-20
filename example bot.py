from aiohttp.helpers import TOKEN
"""from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters.command import Command"""
import logging
import telebot
from telebot import types
import os
from dotenv import load_dotenv

def init_datebase():
    pass

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

user_data = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile=types.KeyboardButton("Профиль")
language=types.KeyboardButton("Язык")
menu.add(profile, language)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_button=types.KeyboardButton("Назад")
back.add(back_button)

@bot.message_handler(content_types=['text'])
def text_messages(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Что тебя интересует?", reply_markup=menu)
    elif message.text == "Профиль":
        bot.send_message(message.chat.id, "Имя: \Дата рождения: \Часовой пояс: \Город рождения: ", reply_markup=menu)


@bot.message_handler(commands=['start'])
def start_message(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Добрый день. Введите имя.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_name)
def ask_name(message):
    user_id = message.chat.id
    user_data[user_id]['name']=message.text
    bot.send_message(message.chat.id, "Введите дату рождения\Формат дд:мм:гггг", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_date)
def ask_date(message):
    user_id = message.chat.id
    user_data[user_id]['date']=message.text
    bot.send_message(message.chat.id, "Введите время рождения\Формат чч:мм", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_time)
def ask_time(message):
    user_id = message.chat.id
    user_data[user_id]['time']=message.text
    bot.send_message(message.chat.id, "Введите часовой пояс\Формат GMT+n", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_timezone)
def ask_timezone(message):
        user_id = message.chat.id
        user_data[user_id]['timezone'] = message.text
        bot.send_message(message.chat.id, "Введите город рождения\Формат страна, город", reply_markup=types.ReplyKeyboardRemove())
bot.infinity_polling()

"""

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/menu", description="Главное меню"),
        BotCommand(command="/profile", description="Профиль"),
        BotCommand(command="/language", description="Язык"),
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я пока только умею повторять твои сообщения!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы сказали: {update.message.text}")


def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()

main()

"""

