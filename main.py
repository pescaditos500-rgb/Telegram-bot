import telebot
from telebot import types
import random
import json
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
COMMISSION = int(os.getenv("COMMISSION", 7))
TURN_TIME = int(os.getenv("TURN_TIME", 30))

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ===== АНТИСПАМ =====
last_action = {}

def anti_spam(uid):
    now = time.time()
    if uid in last_action and now - last_action[uid] < 1:
        return False
    last_action[uid] = now
    return True

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

def create_user(uid, name):
    if uid not in users:
        users[uid] = {
            "nick": name,
            "wins": 0,
            "loses": 0,
            "rating": 1000,
            "hints": 3,
            "last_daily": 0
        }

# ===== ИГРЫ =====
pve_games = {}
pvp_games = {}

# ===== ELO =====
def update_elo(winner, loser):
    K = 32
    r1 = users[winner]["rating"]
    r2 = users[loser]["rating"]

    e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
    e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))

    users[winner]["rating"] = int(r1 + K * (1 - e1))
    users[loser]["rating"] = int(r2 + K * (0 - e2))
    save_data()

# ===== МЕНЮ =====
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("🤖 PvE", "⚔️ PvP")
    m.row("💡 Подсказка", "👤 Профиль")
    m.row("🏆 Топ", "🎁 Daily")
    m.row("🛒 Магазин")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    create_user(uid, message.from_user.first_name)
    save_data()
    bot.send_message(uid, "🎮 Добро пожаловать!", reply_markup=menu())

# ===== PvE =====
@bot.message_handler(func=lambda m: m.text == "🤖 PvE")
def pve_start(message):
    uid = str(message.chat.id)
    if not anti_spam(uid): return

    pve_games[uid] = random.randint(1, 1000)
    bot.send_message(uid, "🤖 Я загадал число 1-1000")

# ===== PvP INVITE =====
@bot.message_handler(func=lambda m: m.text == "⚔️ PvP")
def pvp_invite(message):
    uid = str(message.chat.id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принять матч", callback_data=f"accept_{uid}"))

    bot.send_message(uid, "🎮 Нажми и отправь другу для PvP", reply_markup=kb)

# ===== ACCEPT =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_match(call):
    p1 = call.data.split("_")[1]
    p2 = str(call.message.chat.id)

    if p1 == p2:
        return

    gid = str(time.time())

    pvp_games[gid] = {
        "p1": p1,
        "p2": p2,
        "bet": 10,
        "numbers": {},
        "turn": None,
        "last_move": time.time()
    }

    bot.send_message(p1, "🎯 Введи число 1-1000")
    bot.send_message(p2, "🎯 Введи число 1-1000")

# ===== МАГАЗИН =====
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("5 подскзок — 3⭐", callback_data="buy_5"))
    kb.add(types.InlineKeyboardButton("15 подсказок — 7⭐", callback_data="buy_15"))
    kb.add(types.InlineKeyboardButton("25 подсказок — 11⭐", callback_data="buy_25"))
    kb.add(types.InlineKeyboardButton("50 подсказок (ВЫГОДНО!!!)— 17⭐", callback_data="buy_50"))
    bot.send_message(message.chat.id, "🛒 Магазин", reply_markup=kb)

# ===== ПОКУПКА =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy(call):
    bot.answer_callback_query(call.id)

    prices = {
        "buy_5": (5, 3),
        "buy_15": (15, 7),
        "buy_25": (25, 11),
        "buy_50": (50, 17)
    }

    hints, stars = prices[call.data]

   bot.send_invoice(
    call.message.chat.id,
    "Подсказки",
    f"{hints} подсказок",
    call.data,
    "",  # ⭐ ВАЖНО: пусто!
    "XTR",
    [types.LabeledPrice("Подсказки", stars)]
)
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def pay(message):
    uid = str(message.chat.id)

    data = {
        "buy_5": 5,
        "buy_15": 15,
        "buy_25": 25,
        "buy_50": 50
    }

    payload = message.successful_payment.invoice_payload
    users[uid]["hints"] += data[payload]
    save_data()

    bot.send_message(uid, f"✅ +{data[payload]} подсказок")

# ===== ПОДСКАЗКА =====
@bot.message_handler(func=lambda m: m.text == "💡 Подсказка")
def hint(message):
    uid = str(message.chat.id)

    # PvE
    if uid in pve_games:
        if users[uid]["hints"] <= 0:
            bot.send_message(uid, "❌ Нет подсказок")
            return

        users[uid]["hints"] -= 1
        num = pve_games[uid]
        save_data()

        bot.send_message(uid, f"🔍 Первая цифра: {str(num)[0]}")
        return

    # PvP
    for game in pvp_games.values():
        if uid in [game["p1"], game["p2"]]:
            opponent = game["p1"] if uid == game["p2"] else game["p2"]

            if users[uid]["hints"] <= 0:
                bot.send_message(uid, "❌ Нет подсказок")
                return

            num = game["numbers"].get(opponent)
            if not num:
                bot.send_message(uid, "⏳ Соперник ещё не загадал")
                return

            users[uid]["hints"] -= 1
            save_data()

            bot.send_message(uid, f"🔍 Первая цифра: {str(num)[0]}")
            return

# ===== DAILY =====
@bot.message_handler(func=lambda m: m.text == "🎁 Daily")
def daily(message):
    uid = str(message.chat.id)
    now = time.time()

    if now - users[uid]["last_daily"] < 86400:
        bot.send_message(uid, "⏳ Уже забрал")
        return

    reward = random.randint(1, 7)
    users[uid]["last_daily"] = now
    users[uid]["hints"] += reward
    save_data()

    bot.send_message(uid, f"🎁 +{reward} подсказок")

# ===== ПРОФИЛЬ =====
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    uid = str(message.chat.id)
    u = users[uid]

    bot.send_message(uid,
        f"👤 {u['nick']}\n"
        f"🏆 {u['wins']} | 💀 {u['loses']}\n"
        f"⭐ {u['rating']}\n"
        f"💡 {u['hints']}"
    )

# ===== ТОП =====
@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["rating"], reverse=True)

    text = "🏆 ТОП 10\n\n"
    for i, (uid, u) in enumerate(sorted_users[:10], 1):
        text += f"{i}. {u['nick']} — {u['rating']}\n"

    bot.send_message(message.chat.id, text)

# ===== PvP TIMEOUT =====
def timeout_loop():
    while True:
        now = time.time()

        for gid, game in list(pvp_games.items()):
            if game["turn"] and now - game["last_move"] > TURN_TIME:
                loser = game["turn"]
                winner = game["p1"] if loser == game["p2"] else game["p2"]

                bot.send_message(loser, "⏱ Ты проиграл по времени")
                bot.send_message(winner, "🏆 Победа")

                update_elo(winner, loser)
                del pvp_games[gid]

        time.sleep(5)

threading.Thread(target=timeout_loop, daemon=True).start()

# ===== ОСНОВНАЯ ИГРА =====
@bot.message_handler(func=lambda m: True)
def game(message):
    uid = str(message.chat.id)

    if not anti_spam(uid): return

    # PvE
    if uid in pve_games:
        if not message.text.isdigit(): return

        num = int(message.text)
        target = pve_games[uid]

        if num < target:
            bot.send_message(uid, "⬆️ Больше")
        elif num > target:
            bot.send_message(uid, "⬇️ Меньше")
        else:
            bot.send_message(uid, "🎉 Победа")
            users[uid]["wins"] += 1
            save_data()
            del pve_games[uid]
        return

    # PvP
    for gid, game in pvp_games.items():
        if uid not in [game["p1"], game["p2"]]:
            continue

        if uid not in game["numbers"]:
            if not message.text.isdigit(): return
            num = int(message.text)

            if not 1 <= num <= 1000:
                return

            game["numbers"][uid] = num
            bot.send_message(uid, "✅ Сохранено")

            if len(game["numbers"]) == 2:
                game["turn"] = game["p1"]
                game["last_move"] = time.time()
                bot.send_message(game["p1"], "🎮 Твой ход")
                bot.send_message(game["p2"], "⏳ Ход соперника")
            return

        if game["turn"] != uid:
            bot.send_message(uid, "⏳ Не твой ход")
            return

        if not message.text.isdigit(): return

        guess = int(message.text)
        opponent = game["p1"] if uid == game["p2"] else game["p2"]
        target = game["numbers"][opponent]

        if guess < target:
            bot.send_message(uid, "⬆️ Больше")
        elif guess > target:
            bot.send_message(uid, "⬇️ Меньше")
        else:
            total = game["bet"] * 2
            commission = int(total * COMMISSION / 100)

            bot.send_message(uid, "🏆 Победа")
            bot.send_message(opponent, "💀 Проигрыш")

            update_elo(uid, opponent)

            if ADMIN_ID:
                bot.send_message(ADMIN_ID, f"💰 {commission}")

            del pvp_games[gid]
            return

        game["turn"] = opponent
        game["last_move"] = time.time()
        bot.send_message(opponent, "🎮 Твой ход")

print("🚀 BOT STARTED")
bot.infinity_polling()
