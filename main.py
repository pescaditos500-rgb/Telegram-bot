import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAGG4D7iHwD-tGiu6zsb4qiV-nH7d47cbh4"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== ДАННЫЕ =====
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
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("🚀 Старт", "💡 Подсказка")
    m.row("🛒 Магазин", "📊 Стата")
    m.row("🏆 Топ", "🎁 Daily")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {"wins": 0, "hints": 3, "last": 0}
        save_data()

    bot.send_message(chat_id, "👋 Привет", reply_markup=menu())

# ===== МАГАЗИН =====
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton("5 подсказок — 3⭐", callback_data="buy_5"))
    kb.add(types.InlineKeyboardButton("15 подсказок — 7⭐", callback_data="buy_15"))
    kb.add(types.InlineKeyboardButton("25 подсказок — 11⭐", callback_data="buy_25"))
    kb.add(types.InlineKeyboardButton("🔥 50 подсказок — 17⭐", callback_data="buy_50"))

    bot.send_message(message.chat.id, "🛒 Магазин", reply_markup=kb)

# ===== КНОПКИ ПОКУПКИ (САМОЕ ВАЖНОЕ) =====
@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    print("НАЖАЛИ КНОПКУ:", call.data)
    bot.answer_callback_query(call.id)

    if not call.data.startswith("buy_"):
        return

    prices = {
        "buy_5": (5, 3),
        "buy_15": (15, 7),
        "buy_25": (25, 11),
        "buy_50": (50, 17)
    }

    hints, stars = prices[call.data]

   bot.send_invoice(
    chat_id=call.message.chat.id,
    title="Подсказки",
    description=f"{hints} подсказок",
    payload=call.data,
    currency="XTR",
    prices=[types.LabeledPrice("Подсказки", stars)],
    start_parameter="buy"
)

# ===== ОБЯЗАТЕЛЬНО =====
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

# ===== ПОСЛЕ ОПЛАТЫ =====
@bot.message_handler(content_types=['successful_payment'])
def pay(message):
    chat_id = str(message.chat.id)

    data = {
        "buy_5": 5,
        "buy_15": 15,
        "buy_25": 25,
        "buy_50": 50
    }

    payload = message.successful_payment.invoice_payload

    users[chat_id]["hints"] += data[payload]
    save_data()

    bot.send_message(chat_id, f"✅ +{data[payload]} подсказок")

# ===== ИГРА =====
@bot.message_handler(func=lambda m: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(chat_id, "Я загадал число 1-100")
        return

    if text == "💡 Подсказка":
        if users[chat_id]["hints"] <= 0:
            bot.send_message(chat_id, "❌ Нет подсказок")
            return

        if chat_id not in games:
            bot.send_message(chat_id, "Нажми старт")
            return

        users[chat_id]["hints"] -= 1
        save_data()

        num = games[chat_id]
        bot.send_message(chat_id, f"Первая цифра: {str(num)[0]}")
        return

    if text == "📊 Стата":
        u = users[chat_id]
        bot.send_message(chat_id, f"🏆 {u['wins']}\n💡 {u['hints']}")
        return

    if text == "🏆 Топ":
        top = sorted(users.values(), key=lambda x: x["wins"], reverse=True)
        t = "🏆 ТОП\n"
        for i, u in enumerate(top[:10], 1):
            t += f"{i}. {u['wins']}\n"
        bot.send_message(chat_id, t)
        return

    if text == "🎁 Daily":
        now = time.time()
        if now - users[chat_id]["last"] < 86400:
            bot.send_message(chat_id, "⏳ Уже брал")
            return

        users[chat_id]["last"] = now
        users[chat_id]["hints"] += 2
        save_data()

        bot.send_message(chat_id, "🎁 +2 подсказки")
        return

    if chat_id not in games:
        return

    try:
        guess = int(text)
    except:
        return

    num = games[chat_id]

    if guess < num:
        bot.send_message(chat_id, "🔼 Больше")
    elif guess > num:
        bot.send_message(chat_id, "🔽 Меньше")
    else:
        bot.send_message(chat_id, "🎉 Победа")
        users[chat_id]["wins"] += 1
        save_data()
        del games[chat_id]

print("БОТ РАБОТАЕТ")
bot.infinity_polling()
