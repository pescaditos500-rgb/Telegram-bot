import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAFtvOSoKw9NwTQUYT0IRjUT1vJVKe0c1Hg"
PROVIDER_TOKEN = ""  # вставишь когда появятся Stars

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
    markup.row("🚀 Старт", "🎮 PvP")
    markup.row("💡 Подсказка", "🛒 Магазин")
    markup.row("📊 Статистика", "🏆 Топ игроков")
    markup.row("🎁 Daily gifts")
    return markup

# ===== START =====
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

    bot.send_message(chat_id, "👋 Добро пожаловать!", reply_markup=main_menu())

# ===== DAILY =====
@bot.message_handler(commands=['daily'])
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
    user = users[chat_id]

    bot.send_message(chat_id,
        f"👤 {user['name']}\n🏆 Победы: {user['wins']}\n💡 Подсказки: {user['hints']}"
    )

# ===== ТОП =====
def top(message):
    sorted_users = sorted(users.values(), key=lambda x: x["wins"], reverse=True)

    text = "🏆 ТОП игроков:\n"
    for i, u in enumerate(sorted_users[:10], 1):
        text += f"{i}. {u['name']} — {u['wins']}\n"

    bot.send_message(message.chat.id, text)

# ===== МАГАЗИН =====
def shop(message):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("5 подсказок — 3⭐", callback_data="buy_5"))
    markup.add(types.InlineKeyboardButton("15 подсказок — 7⭐", callback_data="buy_15"))
    markup.add(types.InlineKeyboardButton("25 подсказок — 11⭐", callback_data="buy_25"))
    markup.add(types.InlineKeyboardButton("50 подсказок — 17⭐ 🔥 выгодно", callback_data="buy_50"))

    bot.send_message(message.chat.id, "🛒 Магазин:", reply_markup=markup)

# ===== ПОКУПКА =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy(call):
    if PROVIDER_TOKEN == "":
        bot.send_message(call.message.chat.id, "❌ Stars ещё не подключены")
        return

    prices = {
        "buy_5": (5, 3),
        "buy_15": (15, 7),
        "buy_25": (25, 11),
        "buy_50": (50, 17),
    }

    hints, stars = prices[call.data]

    bot.send_invoice(
        call.message.chat.id,
        title="Покупка подсказок",
        description=f"{hints} подсказок",
        invoice_payload=f"hints_{hints}",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=[types.LabeledPrice(label="Подсказки", amount=stars)]
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
    hints = int(payload.split("_")[1])

    users[chat_id]["hints"] += hints
    save_data()

    bot.send_message(chat_id, f"✅ +{hints} подсказок")

# ===== ОСНОВНАЯ ЛОГИКА =====
@bot.message_handler(func=lambda message: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(chat_id, "🎮 Я загадал число от 1 до 100!")
        return

    if text == "🎮 PvP":
        bot.send_message(chat_id, "Пока не готово")
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

    if chat_id not in games:
        bot.send_message(chat_id, "Нажми 🚀 Старт")
        return

    try:
        guess = int(text)
    except:
        bot.send_message(chat_id, "Введи число")
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
print("БОТ РАБОТАЕТ")
bot.polling()
