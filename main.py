from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host='0.0.0.0', port=3000)

def keep_alive():
    t = Thread(target=run)
    t.start()
import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAFLMkthqndOFaPpe470e5lwsgnPr6AbDpo"  # <-- вставь сюда свой токен
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ====== Загрузка и сохранение ======
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
pvp_games = {}

# ====== Главное меню ======
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Старт", "🎮 PvP")
    markup.row("💡 Подсказка", "🛒 Магазин")
    markup.row("📊 Стата", "🏆 Топ")
    markup.row("🎁 Daily")
    return markup

# ====== START ======
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {
            "name": "Без имени",
            "wins": 0,
            "hints": 3,
            "last_daily": 0,
            "can_rename": True
        }
        save_data()

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в игру!\nНажми 🚀 Старт чтобы начать",
        reply_markup=main_menu()
    )

# ====== DAILY ======
@bot.message_handler(commands=['daily'])
def daily(message):
    chat_id = str(message.chat.id)
    now = time.time()
    last = users[chat_id].get("last_daily", 0)

    if now - last < 86400:
        bot.send_message(message.chat.id, "⏳ Уже получал сегодня")
        return

    users[chat_id]["hints"] += 3
    users[chat_id]["last_daily"] = now
    users[chat_id]["can_rename"] = True
    save_data()

    bot.send_message(message.chat.id, "🎁 +3 подсказки и можно сменить ник")

# ====== Никнейм ======
@bot.message_handler(commands=['setname'])
def setname(message):
    chat_id = str(message.chat.id)

    if not users[chat_id].get("can_rename", False):
        bot.send_message(chat_id, "❌ Сменить ник можно через /daily")
        return

    try:
        new_name = message.text.split(maxsplit=1)[1]
    except:
        bot.send_message(chat_id, "Используй: /setname Ник")
        return

    for user in users.values():
        if user["name"].lower() == new_name.lower():
            bot.send_message(chat_id, "❌ Ник занят")
            return

    users[chat_id]["name"] = new_name
    users[chat_id]["can_rename"] = False
    save_data()

    bot.send_message(chat_id, f"✅ Ник: {new_name}")

# ====== Статистика ======
@bot.message_handler(commands=['stats'])
def stats(message):
    chat_id = str(message.chat.id)
    user = users[chat_id]

    bot.send_message(
        message.chat.id,
        f"👤 {user['name']}\n🏆 Победы: {user['wins']}\n💡 Подсказки: {user['hints']}"
    )

# ====== Топ игроков ======
@bot.message_handler(commands=['top'])
def top(message):
    sorted_users = sorted(users.values(), key=lambda x: x["wins"], reverse=True)

    text = "🏆 ТОП игроков:\n\n"
    for i, u in enumerate(sorted_users[:10], 1):
        text += f"{i}. {u['name']} — {u['wins']}\n"

    bot.send_message(message.chat.id, text)

# ====== PvP ======
@bot.message_handler(commands=['challenge'])
def challenge(message):
    chat_id = str(message.chat.id)

    try:
        name = message.text.split(maxsplit=1)[1]
    except:
        bot.send_message(chat_id, "Используй: /challenge Ник")
        return

    for uid, user in users.items():
        if user["name"].lower() == name.lower():
            number = random.randint(1, 100)

            pvp_games[chat_id] = {"opponent": uid, "number": number}
            pvp_games[uid] = {"opponent": chat_id, "number": number}

            bot.send_message(message.chat.id, "⚔️ PvP начался!")
            bot.send_message(int(uid), "⚔️ Тебя вызвали на PvP!")
            return

    bot.send_message(chat_id, "❌ Игрок не найден")

# ====== Магазин ======
@bot.message_handler(commands=['shop'])
def shop(message):
    bot.send_message(message.chat.id, "🛒 Магазин будет работать через Telegram Stars.")

# ====== Игра / кнопки ======
@bot.message_handler(func=lambda message: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(message.chat.id, "🎮 Я загадал число от 1 до 100!", reply_markup=main_menu())
        return

    if text == "🎮 PvP":
        bot.send_message(message.chat.id, "Напиши: /challenge Ник игрока", reply_markup=main_menu())
        return

    if text == "🛒 Магазин":
        shop(message)
        return

    if text == "📊 Стата":
        stats(message)
        return

    if text == "🏆 Топ":
        top(message)
        return

    if text == "🎁 Daily":
        daily(message)
        return

    if text == "💡 Подсказка":
        if users[chat_id]["hints"] <= 0:
            bot.send_message(message.chat.id, "❌ Нет подсказок")
            return

        if chat_id not in games:
            bot.send_message(message.chat.id, "Сначала нажми 🚀 Старт")
            return

        users[chat_id]["hints"] -= 1
        number = games[chat_id]

        bot.send_message(message.chat.id, f"💡 Первая цифра: {str(number)[0]}", reply_markup=main_menu())
        return

    # PvP игра
    if chat_id in pvp_games:
        data = pvp_games[chat_id]

        try:
            guess = int(message.text)
        except:
            return

        if guess == data["number"]:
            users[chat_id]["wins"] += 1
            bot.send_message(message.chat.id, "🏆 Ты выиграл PvP!")
            bot.send_message(int(data["opponent"]), "😢 Ты проиграл PvP")

            del pvp_games[chat_id]
            del pvp_games[data["opponent"]]
            save_data()
            return

    # Обычная игра
    if chat_id not in games:
        bot.send_message(message.chat.id, "Напиши 🚀 Старт чтобы начать")
        return

    try:
        guess = int(message.text)
    except:
        bot.send_message(message.chat.id, "Введи число от 1 до 100")
        return

    number = games[chat_id]

    if guess < number:
        bot.send_message(message.chat.id, "🔼 Больше")
    elif guess > number:
        bot.send_message(message.chat.id, "🔽 Меньше")
    else:
        users[chat_id]["wins"] += 1
        save_data()

        bot.send_message(message.chat.id, "🎉 Ты угадал!", reply_markup=main_menu())
        del games[chat_id]

# ====== Запуск ======
keep_alive()
print("БОТ ЗАПУЩЕН 24/7 🚀")
bot.infinity_polling()
