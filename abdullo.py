import telebot
from telebot import types
import requests
from flask import Flask, request

# ==============================
#    НАСТРОЙКИ БОТА
# ==============================
BOT_TOKEN = "ТВОЙ_TOKEN"
CHANNEL_USERNAME = "@myfilmzonehub"
ADMIN_ID = 695839201

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
#  ПРОВЕРКА ПОДПИСКИ
# ==============================

def check_subscription(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}

    try:
        r = requests.get(url, params=params).json()
        status = r["result"]["status"]

        return status in ["member", "administrator", "creator"]

    except:
        return False


# ==============================
#  КНОПКА "ПОДПИСАТЬСЯ"
# ==============================

def subscribe_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔔 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
    kb.add(types.InlineKeyboardButton("♻ Проверить подписку", callback_data="check"))
    return kb


# ==============================
# МЕНЮ ЮЗЕРА
# ==============================

def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎬 Поиск фильма", "🔥 Популярное")
    kb.add("⭐ Избранное")
    return kb


# ==============================
# МЕНЮ АДМИНА
# ==============================

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Сделать рассылку", "📊 Статистика")
    kb.add("🎬 Поиск фильма", "🔥 Популярное")
    return kb


# ==============================
# КОМАНДА /start
# ==============================

@bot.message_handler(commands=["start"])
def welcome(msg):

    # --- проверка подписки ---
    if not check_subscription(msg.from_user.id):
        bot.send_message(
            msg.chat.id,
            "❗ *Чтобы пользоваться ботом — подпишись на наш кино-канал!*",
            parse_mode="Markdown",
            reply_markup=subscribe_keyboard()
        )
        return

    # --- если подписан ---
    welcome_text = (
        "🎬 *Добро пожаловать в PopKorn!* 🍿\n\n"
        "🔥 Здесь тебя ждёт огромный каталог фильмов и сериалов.\n"
        "🔍 Ищи по названию, жанрам и популярности.\n"
        "⭐ Добавляй в избранное, находи новые релизы.\n\n"
        "Готов открыть для себя новое кино? 🎥✨"
    )

    if msg.from_user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "👑 Админ режим активирован", reply_markup=admin_menu())
    else:
        bot.send_message(msg.chat.id, welcome_text, parse_mode="Markdown", reply_markup=user_menu())


# ==============================
# INLINE КНОПКИ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "check")
def recheck(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✔ Подписка подтверждена!")
        bot.send_message(call.message.chat.id, "Теперь ты можешь пользоваться ботом 🎉", reply_markup=user_menu())
    else:
        bot.answer_callback_query(call.id, "❌ Ты ещё не подписался!")
        bot.send_message(call.message.chat.id, "Подпишись на канал:", reply_markup=subscribe_keyboard())


# ==============================
# ОБЩИЕ СООБЩЕНИЯ (ПОСЛЕ ПОДПИСКИ)
# ==============================

@bot.message_handler(func=lambda message: True)
def all_messages(msg):

    # сначала проверяем подписку
    if not check_subscription(msg.from_user.id):
        bot.send_message(
            msg.chat.id,
            "❗ Чтобы пользоваться ботом — обязательно подпишись!",
            reply_markup=subscribe_keyboard()
        )
        return

    # дальше логика бота
    bot.send_message(msg.chat.id, "🔍 Напиши название фильма:", reply_markup=user_menu())


# ==============================
#   WEBHOOK ДЛЯ RENDER
# ==============================

WEBHOOK_HOST = "https://ТВОЙ-RENDER-URL.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

app = Flask(__name__)


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_str = request.stream.read().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# Запуск Flask
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
