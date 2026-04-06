import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = "8710556658:AAEfSZ5sJURMmefbe7Gaxx1wVfEUv2k_Rtw"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== Загрузка =====
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

# ===== Меню =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Старт", "💡 Подсказка")
    markup.row("🛒 Магазин", "📊 Статистика игрока")
    return markup

# ===== Старт =====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {
            "wins": 0,
            "hints": 3
        }
        save_data()

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать!\nНажми 🚀 Старт",
        reply_markup=main_menu()
    )

# ===== Магазин =====
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("5 подсказок — 3⭐", callback_data="buy_5"))
    markup.add(types.InlineKeyboardButton("15 подсказок — 7⭐", callback_data="buy_15"))
    markup.add(types.InlineKeyboardButton("25 подсказок — 11⭐", callback_data="buy_25"))
    markup.add(types.InlineKeyboardButton("🔥 50 подсказок — 17⭐ (ВЫГОДНО)", callback_data="buy_50"))

    bot.send_message(
        message.chat.id,
        "🛒 МАГАЗИН\n\n"
        "5 подсказок — 3⭐\n"
        "15 подсказок — 7⭐\n"
        "25 подсказок — 11⭐\n"
        "🔥 50 подсказок — 17⭐ (ВЫГОДА 22%)",
        reply_markup=markup
    )

# ===== Покупка =====
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
    invoice_payload=call.data,
    currency="XTR",
    prices=[types.LabeledPrice("Подсказки", stars)]
)
    )

# ===== Оплата =====
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    chat_id = str(message.chat.id)
    payload = message.successful_payment.invoice_payload

    if payload == "buy_5":
        users[chat_id]["hints"] += 5
    elif payload == "buy_15":
        users[chat_id]["hints"] += 15
    elif payload == "buy_25":
        users[chat_id]["hints"] += 25
    elif payload == "buy_50":
        users[chat_id]["hints"] += 50

    save_data()

    bot.send_message(message.chat.id, "✅ Покупка успешна!")

# ===== Игра =====
@bot.message_handler(func=lambda message: True)
def game(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🚀 Старт":
        games[chat_id] = random.randint(1, 100)
        bot.send_message(message.chat.id, "Я загадал число от 1 до 100")
        return

    if text == "💡 Подсказка":
        if users[chat_id]["hints"] <= 0:
            bot.send_message(message.chat.id, "❌ Нет подсказок")
            return
        if chat_id not in games:
            bot.send_message(message.chat.id, "Нажми 🚀 Старт")
            return

        users[chat_id]["hints"] -= 1
        number = games[chat_id]
        bot.send_message(message.chat.id, f"Первая цифра: {str(number)[0]}")
        return

    if text == "📊 Стата":
        u = users[chat_id]
        bot.send_message(message.chat.id, f"Победы: {u['wins']}\nПодсказки: {u['hints']}")
        return

    if chat_id not in games:
        return

    try:
        guess = int(text)
    except:
        return

    number = games[chat_id]

    if guess < number:
        bot.send_message(message.chat.id, "Больше")
    elif guess > number:
        bot.send_message(message.chat.id, "Меньше")
    else:
        users[chat_id]["wins"] += 1
        save_data()
        bot.send_message(message.chat.id, "🎉 Угадал!")
        del games[chat_id]

# ===== Запуск =====
print("БОТ ЗАПУЩЕН")
bot.infinity_polling()
