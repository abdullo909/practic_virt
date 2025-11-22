import telebot
from telebot import types
from datetime import datetime


# ========= НАСТРОЙКИ =========
BOT_TOKEN = "8351030266:AAFvywov7-hwoO0Y8lRdktGlzEss2Q-a8uk"
CHANNEL_USERNAME = "myfilmzonehub"     # без @
BOT_ID = 6408109992


bot = telebot.TeleBot(BOT_TOKEN)

# ========= ХРАНЕНИЕ ДАННЫХ =========
users = set()
daily_stats = {}   # количество пользователей по дням

# ========= ПРОВЕРКА ПОДПИСКИ =========
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ========= СТАРТ =========
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id

    # Статистика
    users.add(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    daily_stats[today] = daily_stats.get(today, 0) + 1

    # Проверяем подписку
    if not is_subscribed(user_id):
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME}"))
        btn.add(types.InlineKeyboardButton("✔️ Проверить", callback_data="check_sub"))
        bot.send_message(
            user_id,
            "🔥 Чтобы использовать бота — подпишись на наш канал!",
            reply_markup=btn
        )
        return

    send_main_menu(user_id)

def send_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎬 Фильмы", "📺 Сериалы", "🔥 Аниме")
    bot.send_message(user_id, "Выбери категорию 👇", reply_markup=markup)

# ========= КНОПКИ МЕНЮ =========
@bot.message_handler(func=lambda m: m.text in ["🎬 Фильмы", "📺 Сериалы", "🔥 Аниме"])
def send_videos(message):
    cat = message.text

    # Примеры видосов — без ссылок, "как у популярных ботов"
    if cat == "🎬 Фильмы":
        items = ["Фильм 1", "Фильм 2", "Фильм 3"]
    elif cat == "📺 Сериалы":
        items = ["Сериал 1", "Сериал 2", "Сериал 3"]
    else:
        items = ["Аниме 1", "Аниме 2", "Аниме 3"]

    markup = types.InlineKeyboardMarkup()
    for i in items:
        markup.add(types.InlineKeyboardButton(i, url="https://t.me/myfilmzonehub"))

    bot.send_message(message.chat.id, "Выбери:", reply_markup=markup)

# ========= ПРОВЕРКА ПОДПИСКИ (кнопка) =========
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check(call):
    if is_subscribed(call.message.chat.id):
        bot.answer_callback_query(call.id, "✔️ Подписка подтверждена!")
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Не подписан!")

# ========= КОМАНДА /users =========
@bot.message_handler(commands=["users"])
def cmd_users(message):
    if message.chat.id != BOT_ID:
        return bot.send_message(message.chat.id, "❌ Команда только для владельца бота")
    bot.send_message(message.chat.id, f"👥 Всего пользователей: {len(users)}")

# ========= КОМАНДА /stats =========
@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    if message.chat.id != BOT_ID:
        return bot.send_message(message.chat.id, "❌ Команда только для владельца бота")

    text = "📊 Статистика по дням:\n\n"
    for day, count in daily_stats.items():
        text += f"{day}: {count}\n"

    bot.send_message(message.chat.id, text)

# ========= КОМАНДА /post (расширенная) =========

# Шаг 1 — начинаем пост
@bot.message_handler(commands=["post"])
def cmd_post(message):
    if message.chat.id != BOT_ID:
        return bot.send_message(message.chat.id, "❌ Команда только для владельца бота")

    bot.send_message(message.chat.id, "📸 Отправь фото для поста:")
    bot.register_next_step_handler(message, post_get_photo)

# Шаг 2 — получаем фото
def post_get_photo(message):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Это не фото. Отправь нормальное изображение.")
        return bot.register_next_step_handler(message, post_get_photo)

    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "📝 Теперь отправь описание поста:")
    bot.register_next_step_handler(message, post_get_caption, file_id)

# Шаг 3 — получаем описание
def post_get_caption(message, file_id):
    caption = message.text
    bot.send_message(message.chat.id, "🔗 Теперь отправь URL ссылки для кнопки:")
    bot.register_next_step_handler(message, post_get_url, file_id, caption)

# Шаг 4 — кнопка + отправка поста
def post_get_url(message, file_id, caption):
    url = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Смотреть", url=url))

    try:
        bot.send_photo(
            f"@{CHANNEL_USERNAME}",
            file_id,
            caption=caption,
            reply_markup=markup
        )

        bot.send_message(message.chat.id, "✔️ Пост успешно отправлен!")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка отправки: {e}\n"
                                        "Проверь, что бот админ канала.")

print("Бот запущен!")
bot.infinity_polling()