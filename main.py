import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAGG4D7iHwD-tGiu6zsb4qiV-nH7d47cbh4"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== ЗАГРУЗКА =====
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

# ===== МЕНЮ =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Старт", "💡 Подсказка")
    markup.row("🛒 Магазин", "📊 Статистика")
    markup.row("🏆 Топ игроков", "🎁 Daily gifts")
    return markup

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {
            "wins": 0,
            "hints": 3,
            "last_daily": 0
        }
        save_data()

    bot.send_message(chat_id, "👋 Добро пожаловать!", reply_markup=main_menu())

# ===== DAILY =====
def daily(message):
    chat_id = str(message.chat.id)
    now = time.time()
    last = users[chat_id].get("last_daily", 0)

    if now - last < 86400:
        bot.send_message(chat_id, "⏳ Уже получал сегодня")
        return

    users[chat_id]["hints"] += 2
    users[chat_id]["last_daily"] = now
    save_data()

    bot.send_message(chat_id, "🎁 +2 подсказки")

# ===== СТАТИСТИКА =====
def stats(message):
    chat_id = str(message.chat.id)
    u = users[chat_id]

    bot.send_message(chat_id,
        f"🏆 Победы: {u['wins']}\n💡 Подсказки: {u['hints']}"
    )

# ===== ТОП =====
def top(message):
    sorted_users = sorted(users.values(), key=lambda x: x["wins"], reverse=True)

    text = "🏆 ТОП игроков:\n"
    for i, u in enumerate(sorted_users[:10], 1):
        text += f"{i}. Игрок — {u['wins']}\n"

    bot.send_message(message.chat.id, text)

# ===== МАГАЗИН =====
def shop(message):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("5 подсказок — 3⭐", callback_data="buy_5"))
    markup.add(types.InlineKeyboardButton("15 подсказок — 7⭐", callback_data="buy_15"))
    markup.add(types.InlineKeyboardButton("25 подсказок — 11⭐", callback_data="buy_25"))
    markup.add(types.InlineKeyboardButton("🔥 50 подсказок — 17⭐ (самый выгодный)", callback_data="buy_50"))

    bot.send_message(
        message.chat.id,
        "🛒 МАГАЗИН\n\n"
        "5 подсказок — 3⭐\n"
        "15 подсказок — 7⭐\n"
        "25 подсказок — 11⭐\n"
        "🔥 50 подсказок — 17⭐ (самый выгодный вариант)",
        reply_markup=markup
    )

# ===== ПОКУПКА (STARS) =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy(call):
    prices = {
        "buy_5": (5, 3),
        "buy_15": (15, 7),
        "buy_25": (25, 11),
        "buy_50": (50, 17)
    }

    hints, stars = prices[call.data]

    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="Покупка подсказок",
        description=f"{hints} подсказок",
        payload=call.data,
        currency="XTR",
        prices=[types.LabeledPrice("Подсказки", stars)]
    )

# ===== ОБЯЗАТЕЛЬНО =====
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ===== УСПЕШНАЯ ОПЛАТА =====
@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    chat_id = str(message.chat.id)
    payload = message.successful_payment.invoice_payload

    hints_map = {
        "buy_5": 5,
        "buy_15": 15,
        "buy_25": 25,
        "buy_50": 50
    }

    users[chat_id]["hints"] += hints_map[payload]
    save_data()

    bot.send_message(chat_id, f"✅ Оплата прошла! +{hints_map[payload]} подсказок")

# ===== ИГРА =====
@bot.message_handler(func=lambda message: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(chat_id, "🎮 Я загадал число от 1 до 100!")
        return

    if text == "💡 Подсказка":
        if users[chat_id]["hints"] <= 0:
            bot.send_message(chat_id, "❌ Нет подсказок")
            return

        if chat_id not in games:
            bot.send_message(chat_id, "Сначала нажми 🚀 Старт")
            return

        users[chat_id]["hints"] -= 1
        save_data()

        number = games[chat_id]
        bot.send_message(chat_id, f"💡 Первая цифра: {str(number)[0]}")
        return

    if text == "🛒 Магазин":
        shop(message)
        return

    if text == "📊 Статистика":
        stats(message)
        return

    if text == "🏆 Топ игроков":
        top(message)
        return

    if text == "🎁 Daily gifts":
        daily(message)
        return

    if chat_id not in games:
        bot.send_message(chat_id, "Нажми 🚀 Старт")
        return

    try:
        guess = int(text)
    except:
        bot.send_message(chat_id, "Введи число от 1 до 100")
        return

    number = games[chat_id]

    if guess < number:
        bot.send_message(chat_id, "🔼 Больше")
    elif guess > number:
        bot.send_message(chat_id, "🔽 Меньше")
    else:
        users[chat_id]["wins"] += 1
        save_data()
        bot.send_message(chat_id, "🎉 Ты угадал!")
        del games[chat_id]

# ===== ЗАПУСК =====
print("БОТ ЗАПУЩЕН 🚀")
bot.infinity_polling()
