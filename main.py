import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "ТВОЙ_ТОКЕН"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ====== Загрузка ======
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

# ====== МЕНЮ ======
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Старт", "💡 Подсказка")
    markup.row("🛒 Магазин")
    markup.row("📊 Статистика", "🏆 Топ игроков")
    markup.row("🎁 Daily")
    return markup

# ====== START ======
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {
            "name": "Игрок",
            "wins": 0,
            "hints": 3,
            "last_daily": 0
        }
        save_data()

    bot.send_message(message.chat.id, "👋 Добро пожаловать!", reply_markup=main_menu())

# ====== DAILY ======
@bot.message_handler(commands=['daily'])
def daily(message):
    chat_id = str(message.chat.id)
    now = time.time()

    if now - users[chat_id].get("last_daily", 0) < 86400:
        bot.send_message(message.chat.id, "⏳ Уже получал сегодня")
        return

    users[chat_id]["hints"] += 2
    users[chat_id]["last_daily"] = now
    save_data()

    bot.send_message(message.chat.id, "🎁 +2 подсказки!")

# ====== СТАТА ======
def stats_func(message):
    chat_id = str(message.chat.id)
    user = users[chat_id]

    bot.send_message(
        message.chat.id,
        f"👤 {user['name']}\n🏆 Победы: {user['wins']}\n💡 Подсказки: {user['hints']}"
    )

# ====== ТОП ======
def top_func(message):
    sorted_users = sorted(users.values(), key=lambda x: x["wins"], reverse=True)

    text = "🏆 ТОП игроков:\n\n"
    for i, u in enumerate(sorted_users[:10], 1):
        text += f"{i}. {u['name']} — {u['wins']}\n"

    bot.send_message(message.chat.id, text)

# ====== МАГАЗИН ======
def shop_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💡 5 подсказок — 3⭐","💡 10 подсказок — 5⭐","💡 25 подсказок — 12⭐", callback_data="buy_hints"))
    return markup

@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    bot.send_message(message.chat.id, "🛒 Магазин:", reply_markup=shop_menu())

# ====== ОПЛАТА (Stars) ======
@bot.callback_query_handler(func=lambda call: call.data == "buy_hints")
def buy_hints(call):
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="Покупка подсказок",
        description="5 подсказок",
        invoice_payload="hints_5",
        currency="XTR",
        prices=[types.LabeledPrice("Подсказки", 10)]
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    chat_id = str(message.chat.id)

    if message.successful_payment.invoice_payload == "hints_5":
        users[chat_id]["hints"] += 5
        save_data()

        bot.send_message(message.chat.id, "✅ Оплата прошла! +5 подсказок")

# ====== ИГРА ======
@bot.message_handler(func=lambda message: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if chat_id not in users:
        start(message)
        return

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(message.chat.id, "🎮 Я загадал число от 1 до 100!")
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
        bot.send_message(message.chat.id, f"💡 Первая цифра: {str(number)[0]}")
        save_data()
        return

    if text == "📊 Статистика":
        stats_func(message)
        return

    if text == "🏆 Топ игроков":
        top_func(message)
        return

    if text == "🎁 Daily":
        daily(message)
        return

    # угадывание
    if chat_id not in games:
        bot.send_message(message.chat.id, "Нажми 🚀 Старт")
        return

    try:
        guess = int(text)
    except:
        bot.send_message(message.chat.id, "Введи число")
        return

    number = games[chat_id]

    if guess < number:
        bot.send_message(message.chat.id, "🔼 Больше")
    elif guess > number:
        bot.send_message(message.chat.id, "🔽 Меньше")
    else:
        users[chat_id]["wins"] += 1
        save_data()
        bot.send_message(message.chat.id, "🎉 Угадал!")
        del games[chat_id]

# ====== ЗАПУСК ======
print("БОТ С ПЛАТЕЖАМИ ЗАПУЩЕН 🚀")
bot.infinity_polling()
