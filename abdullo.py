import telebot
from telebot import types

# =======================
#    НАСТРОЙКИ
# =======================
BOT_TOKEN = "8567077313:AAFquTN6WU9GqXrgA38oOzULJfB5d4hAecM"
CHANNEL_USERNAME = "myfilmzonehub"   # без @
ADMIN_ID = 6408109992                # твой ID

bot = telebot.TeleBot(BOT_TOKEN)


# =======================
#    ПРОВЕРКА ПОДПИСКИ
# =======================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =======================
#     СООБЩЕНИЕ О ПОДПИСКЕ
# =======================
def send_subscribe_message(user_id):
    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME}"))
    btn.add(types.InlineKeyboardButton("✔ Проверить", callback_data="check_sub"))

    bot.send_message(
        user_id,
        "🔥 Чтобы пользоваться ботом — подпишись на наш канал!",
        reply_markup=btn
    )


# =======================
#         СТАРТ
# =======================
@bot.message_handler(commands=["start"])
def start(message):

    if not is_subscribed(message.chat.id):
        send_subscribe_message(message.chat.id)
        return

    send_main_menu(message.chat.id)


# =======================
#     ГЛАВНОЕ МЕНЮ
# =======================
def send_main_menu(user_id):

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(
        types.KeyboardButton("🎬 Фильмы"),
        types.KeyboardButton("📺 Сериалы"),
        types.KeyboardButton("🔥 Аниме")
    )
    menu.add(types.KeyboardButton("🔍 Поиск"))

    bot.send_message(user_id, "Выбери категорию 👇", reply_markup=menu)


# =======================
#    КНОПКА ПРОВЕРКИ
# =======================
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):

    if is_subscribed(call.message.chat.id):
        bot.answer_callback_query(call.id, "✔ Подписка подтверждена!")
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны!")
        send_subscribe_message(call.message.chat.id)


# =======================
#     КАТЕГОРИИ
# =======================
@bot.message_handler(func=lambda m: m.text in ["🎬 Фильмы", "📺 Сериалы", "🔥 Аниме"])
def category(message):

    if not is_subscribed(message.chat.id):
        return send_subscribe_message(message.chat.id)

    name = message.text

    if name == "🎬 Фильмы":
        items = ["Фильм 1", "Фильм 2", "Фильм 3"]
    elif name == "📺 Сериалы":
        items = ["Сериал 1", "Сериал 2", "Сериал 3"]
    else:
        items = ["Аниме 1", "Аниме 2", "Аниме 3"]

    markup = types.InlineKeyboardMarkup()
    for i in items:
        markup.add(types.InlineKeyboardButton(i, url=f"https://t.me/{CHANNEL_USERNAME}"))

    bot.send_message(message.chat.id, "Выбери:", reply_markup=markup)


# =======================
#     ПОИСК
# =======================
@bot.message_handler(func=lambda m: m.text == "🔍 Поиск")
def search(message):

    if not is_subscribed(message.chat.id):
        return send_subscribe_message(message.chat.id)

    bot.send_message(message.chat.id, "Введите название фильма:")
    bot.register_next_step_handler(message, do_search)


def do_search(message):
    query = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Смотреть 🔗", url=f"https://t.me/{CHANNEL_USERNAME}"))

    bot.send_message(message.chat.id, f"Результат по запросу: {query}", reply_markup=markup)


# =======================
#     /post ДЛЯ АДМИНА
# =======================
@bot.message_handler(commands=["post"])
def post_start(message):
    if message.chat.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ!")

    bot.send_message(message.chat.id, "📸 Отправь фото для поста:")
    bot.register_next_step_handler(message, post_photo)


def post_photo(message):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Нужно фото. Отправьте ещё раз.")
        return bot.register_next_step_handler(message, post_photo)

    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✏ Введи описание:")
    bot.register_next_step_handler(message, post_caption, file_id)


def post_caption(message, file_id):
    caption = message.text
    bot.send_message(message.chat.id, "🔗 Введи URL кнопки:")
    bot.register_next_step_handler(message, post_url, file_id, caption)


def post_url(message, file_id, caption):
    url = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶ Смотреть", url=url))

    try:
        bot.send_photo(
            f"@{CHANNEL_USERNAME}",
            file_id,
            caption=caption,
            reply_markup=markup
        )
        bot.send_message(message.chat.id, "✔ Пост отправлен!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


# =======================
#       СТАРТ БОТА
# =======================
print("BOT RUNNING...")
bot.infinity_polling()
