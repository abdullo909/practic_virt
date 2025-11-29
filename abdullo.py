import telebot
from telebot import types
from flask import Flask, request

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "ТВОЙ_ТОКЕН"
CHANNEL_USERNAME = "myfilmzonehub"      # без @
ADMIN_ID = 123456789                    # твой Telegram ID (замени!)

WEBHOOK_HOST = "https://ИМЯ_СЕРВИСА.onrender.com"
WEBHOOK_URL = f"{WEBHOOK_HOST}/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ============ МЕНЮ ============

def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Поиск", "🔥 Популярное")
    kb.add("⭐ Избранное")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📢 Пост", "📊 Статистика")
    kb.add("🔙 В меню")
    return kb


# ============ ПРОВЕРКА ПОДПИСКИ ============
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False


# ============ КОМАНДА /start ============
@bot.message_handler(commands=['start'])
def start(msg):
    user = msg.from_user

    greeting_text = (
        "🎬 *Добро пожаловать в PopKorn!* 🍿\n\n"
        "🔥 Здесь тебя ждёт огромный каталог фильмов и сериалов.\n"
        "🔍 Ищи по названию, жанрам и популярности.\n"
        "⭐ Добавляй в избранное, находи новые релизы.\n\n"
        "Готов открыть для себя новое кино? 🎥✨"
    )

    # Если админ
    if user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "👑 *Админ-панель активирована*", parse_mode="Markdown",
                        reply_markup=admin_menu())
        return

    # Если обычный юзер
    bot.send_message(msg.chat.id, greeting_text, parse_mode="Markdown", reply_markup=user_menu())


# ============ ОБРАБОТКА ЛЮБОЙ КНОПКИ ============
@bot.message_handler(func=lambda m: True)
def handle_all(msg):
    user_id = msg.from_user.id

    # Проверяем подписку
    if not check_subscription(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME}"))
        kb.add(types.InlineKeyboardButton("✔ Проверить", callback_data="check_sub"))

        bot.send_message(msg.chat.id,
                        "❗ Чтобы пользоваться ботом — подпишись на наш канал.",
                        reply_markup=kb)
        return

    # --- если подписан, ответы ---
    if msg.text == "🔍 Поиск":
        bot.send_message(msg.chat.id, "🔎 Напиши название фильма…")
    elif msg.text == "🔥 Популярное":
        bot.send_message(msg.chat.id, "🔥 Самые популярные фильмы недели…")
    elif msg.text == "⭐ Избранное":
        bot.send_message(msg.chat.id, "⭐ Избранное пока пусто…")
    else:
        bot.send_message(msg.chat.id, "🤖 Я пока не знаю такой команды.")


# ============ КНОПКА "ПРОВЕРИТЬ" ============
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Проверка прошла — доступ открыт!", reply_markup=user_menu())
    else:
        bot.answer_callback_query(call.id, "❗ Подпишись на канал!", show_alert=True)


# ============ FLASK WEBHOOK ============

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200


@app.route('/', methods=['GET'])
def index():
    return "Bot is running!", 200


# ============ ЗАПУСК ============
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    app.run(host="0.0.0.0", port=10000)
