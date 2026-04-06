import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAHyqYRakpbRG8c_3gC9iwmETjfWaIVhIis"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== загрузка =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

users = load_data()
games = {}

# ===== меню =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Старт", "💡 Подсказка")
    markup.row("🛒 Магазин", "📊 Статистика")
    return markup

# ===== старт =====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {
            "wins": 0,
            "hints": 3
        }
        save_data()

    bot.send_message(message.chat.id, "Привет!", reply_markup=main_menu())

# ===== статистика =====
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    chat_id = str(message.chat.id)
    user = users[chat_id]

    bot.send_message(
        message.chat.id,
        f"🏆 Победы: {user['wins']}\n💡 Подсказки: {user['hints']}"
    )

# ===== магазин =====
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    text = (
        "🛒 МАГАЗИН\n\n"
        "5 подсказок — 3 ⭐\n"
        "15 подсказок — 7 ⭐\n"
        "25 подсказок — 11 ⭐\n"
        "50 подсказок — 17 ⭐ 🔥 (самый выгодный вариант)\n\n"
        "Покупка находится в разработке 😎"
    )

    bot.send_message(message.chat.id, text)

# ===== старт игры =====
@bot.message_handler(func=lambda m: m.text == "🚀 Старт")
def start_game(message):
    chat_id = str(message.chat.id)

    games[chat_id] = random.randint(1, 100)

    bot.send_message(message.chat.id, "Я загадал число от 1 до 100!")

# ===== подсказка =====
@bot.message_handler(func=lambda m: m.text == "💡 Подсказка")
def hint(message):
    chat_id = str(message.chat.id)

    if chat_id not in games:
        bot.send_message(message.chat.id, "Сначала нажми 🚀 Старт")
        return

    if users[chat_id]["hints"] <= 0:
        bot.send_message(message.chat.id, "❌ Нет подсказок")
        return

    users[chat_id]["hints"] -= 1
    number = games[chat_id]

    bot.send_message(message.chat.id, f"Первая цифра: {str(number)[0]}")
    save_data()

# ===== угадывание =====
@bot.message_handler(func=lambda m: True)
def game(message):
    chat_id = str(message.chat.id)

    if chat_id not in games:
        return

    try:
        guess = int(message.text)
    except:
        return

    number = games[chat_id]

    if guess < number:
        bot.send_message(message.chat.id, "🔼 Больше")
    elif guess > number:
        bot.send_message(message.chat.id, "🔽 Меньше")
    else:
        bot.send_message(message.chat.id, "🎉 Ты угадал!")
        users[chat_id]["wins"] += 1
        save_data()
        del games[chat_id]

print("БОТ РАБОТАЕТ")
bot.infinity_polling()
