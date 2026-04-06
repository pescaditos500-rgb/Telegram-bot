import telebot
from telebot import types
import random
import json
import os

TOKEN = "8710556658:AAHyqYRakpbRG8c_3gC9iwmETjfWaIVhIis"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

users = load_data()
games = {}

def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🚀 Старт", "💡 Подсказка")
    m.add("🛒 Магазин", "📊 Статистика")
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid not in users:
        users[uid] = {"wins": 0, "hints": 3}
        save_data()

    bot.send_message(msg.chat.id, "Бот запущен 🚀", reply_markup=menu())

# ===== МАГАЗИН =====
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(msg):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("5 — 3⭐", callback_data="b5"))
    kb.add(types.InlineKeyboardButton("15 — 7⭐", callback_data="b15"))
    kb.add(types.InlineKeyboardButton("25 — 11⭐", callback_data="b25"))
    kb.add(types.InlineKeyboardButton("🔥 50 — 17⭐ (ВЫГОДНО)", callback_data="b50"))

    bot.send_message(
        msg.chat.id,
        "МАГАЗИН:\n\n50 подсказок — ВЫГОДА 22% 🔥",
        reply_markup=kb
    )

# ===== ПОКУПКА =====
@bot.callback_query_handler(func=lambda c: True)
def buy(call):
    data = call.data

    prices = {
        "b5": (5, 3),
        "b15": (15, 7),
        "b25": (25, 11),
        "b50": (50, 17)
    }

    if data not in prices:
        return

    hints, stars = prices[data]

    bot.send_invoice(
        call.message.chat.id,
        "Покупка",
        f"{hints} подсказок",
        data,
        "XTR",
        [types.LabeledPrice("Подсказки", stars)]
    )

@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def success(msg):
    uid = str(msg.chat.id)
    data = msg.successful_payment.invoice_payload

    give = {
        "b5": 5,
        "b15": 15,
        "b25": 25,
        "b50": 50
    }

    users[uid]["hints"] += give[data]
    save_data()

    bot.send_message(msg.chat.id, "Оплата прошла ✅")

# ===== ИГРА =====
@bot.message_handler(func=lambda m: True)
def game(msg):
    uid = str(msg.chat.id)

    if uid not in users:
        return

    if msg.text == "🚀 Старт":
        games[uid] = random.randint(1, 100)
        bot.send_message(msg.chat.id, "Я загадал число")
        return

    if msg.text == "💡 Подсказка":
        if users[uid]["hints"] <= 0:
            bot.send_message(msg.chat.id, "Нет подсказок")
            return

        if uid not in games:
            return

        users[uid]["hints"] -= 1
        bot.send_message(msg.chat.id, "Первая цифра: " + str(games[uid])[0])
        return

    if msg.text == "📊 Стата":
        u = users[uid]
        bot.send_message(msg.chat.id, f"Победы: {u['wins']}\nПодсказки: {u['hints']}")
        return

    if uid not in games:
        return

    try:
        n = int(msg.text)
    except:
        return

    num = games[uid]

    if n < num:
        bot.send_message(msg.chat.id, "Больше")
    elif n > num:
        bot.send_message(msg.chat.id, "Меньше")
    else:
        users[uid]["wins"] += 1
        save_data()
        bot.send_message(msg.chat.id, "Ты угадал 🎉")
        del games[uid]

print("БОТ РАБОТАЕТ")
bot.infinity_polling()
