import telebot
from telebot import types
import sqlite3
from datetime import datetime

# =======================
#   НАСТРОЙКИ
# =======================
BOT_TOKEN = "8567077313:AAFquTN6WU9GqXrgA38oOzULJfB5d4hAecM"
CHANNEL_USERNAME = "@myfilmzonehub"
ADMIN_ID = 695839201   # <-- твой админ айди

bot = telebot.TeleBot(BOT_TOKEN)


# =======================
#   БАЗА ДАННЫХ
# =======================
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    reg_date TEXT
)
""")
conn.commit()


def add_user(user):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()


# =======================
#   ПРОВЕРКА ПОДПИСКИ
# =======================
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "creator", "administrator"]
    except:
        return False


# =======================
#   ГЛАВНОЕ МЕНЮ ЮЗЕРА
# =======================
def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔥 Найти фильм", "🎬 Новинки")
    kb.add("❤️ Рекомендации", "📤 Поделиться ботом")
    return kb


# =======================
#   МЕНЮ АДМИНА
# =======================
def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 Создать пост", "🖼 Загрузить фото")
    kb.add("📊 Статистика", "👥 Пользователи")
    kb.add("⬅️ В обычный режим")
    return kb


# =======================
#   КОМАНДА /START
# =======================
@bot.message_handler(commands=['start'])
def start(msg):
    user = msg.from_user
    add_user(user)

    # Проверка подписки
    if not is_subscribed(user.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔗 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        kb.add(types.InlineKeyboardButton("✔️ Проверить", callback_data="check_sub"))

        bot.send_message(
            msg.chat.id,
            "⚠️ Чтобы пользоваться ботом — подпишись на канал!",
            reply_markup=kb
        )
        return

    # Админ или обычный юзер?
    if user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "👑 *Админ-панель активирована*", parse_mode="Markdown", reply_markup=admin_menu())
    else:
        bot.send_message(msg.chat.id,
                        "🎬 *Добро пожаловать!* \n\n"
                        "Здесь ты можешь искать фильмы, смотреть рекомендации и открывать для себя новое кино 🍿",
                        parse_mode="Markdown",
                        reply_markup=user_menu())


# =======================
#   INLINE CALLBACK
# =======================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data == "check_sub":
        if is_subscribed(c.from_user.id):
            bot.delete_message(c.message.chat.id, c.message.message_id)
            start(c.message)
        else:
            bot.answer_callback_query(c.id, "❌ Вы не подписаны!")


# =======================
#   АДМИН КОМАНДЫ
# =======================
@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
def admin_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    bot.send_message(msg.chat.id, f"👥 Всего пользователей: *{total}*", parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    bot.send_message(msg.chat.id,
                    f"📊 *Статистика бота*\n\n"
                    f"👥 Пользователей: {total}\n"
                    f"📅 Запущено: {datetime.now().strftime('%Y-%m-%d')}",
                    parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "📝 Создать пост")
def post(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "✏️ Напиши текст поста:")


# =======================
#   СТАРТ БОТА
# =======================
bot.infinity_polling()
