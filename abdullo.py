import telebot
from telebot import types

# =======================
#    НАСТРОЙКИ
# =======================
BOT_TOKEN = "8567077313:AAFquTN6WU9GqXrgA38oOzULJfB5d4hAecM"
CHANNEL_USERNAME = "myfilmzonehub"   # без @
ADMIN_ID = 6408109992                # замени на свой Telegram ID

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
#    СТАРТ
# =======================
@bot.message_handler(commands=["start"])
def start(message):

    if not is_subscribed(message.chat.id):
        send_subscribe_message(message.chat.id)
        return

    send_main_menu(message.chat.id)


# =======================
#   СООБЩЕНИЕ О ПОДПИСКЕ
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
#    ГЛАВНОЕ МЕНЮ
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

    # Псевдо поиск (как у популярных ботов)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Смотреть 🔗", url=f"https://t.me/{CHANNEL_USERNAME}"))

    bot.send_message(message.chat.id, f"Результат по запросу: {query}", reply_markup=markup)


# =======================
#     КОМАНДА /post
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


# ======================
#   СТАРТ
# ======================
print("BOT RUNNING...")
bot.infinity_polling()



import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command

TOKEN = "8569453490:AAGDgQRfxfxQ2IwYRgspPu-Rz7bqyTbXMcQ"
ADMIN_ID = 6408109992  # ← впиши сюда свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    username = message.from_user.username
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    # сообщение пользователю
    await message.answer(
        f"Привет, {first_name}!\n"
        f"Твой username: @{username}\n"
        f"Твой ID: {user_id}"
    )

    # сообщение админу
    await bot.send_message(
        ADMIN_ID,
        f"Новый пользователь!\n"
        f"Имя: {first_name}\n"
        f"Username: @{username}\n"
        f"ID: {user_id}"
    )

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())



import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8569453490:AAGDgQRfxfxQ2IwYRgspPu-Rz7bqyTbXMcQ"
ADMIN_ID = 6408109992   # ← ВСТАВЬ СВОЙ ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# --- Кнопка регистрации ---
register_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Поделиться контактом для регистрации", request_contact=True)]
    ],
    resize_keyboard=True
)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    username = message.from_user.username
    first_name = message.from_user.first_name
    user_id = message.from_user.id

    # Сообщение пользователю
    await message.answer(
        "Добро пожаловать!\n\n"
        "Чтобы пройти регистрацию — нажмите кнопку ниже 👇\n"
        "Бот автоматически получит ваш номер телефона.",
        reply_markup=register_kb
    )

    # Сообщение админу
    await bot.send_message(
        ADMIN_ID,
        f"🔔 Новый пользователь!\n"
        f"Имя: {first_name}\n"
        f"Username: @{username}\n"
        f"ID: {user_id}"
    )

@router.message()
async def get_contact(message: types.Message):
    if message.contact:  # Пользователь поделился номером
        phone = message.contact.phone_number
        user = message.from_user

        # Сообщение пользователю
        await message.answer("Спасибо! Регистрация завершена ✔️")

        # Уведомление админу
        await bot.send_message(
            ADMIN_ID,
            f"📞 Пользователь завершил регистрацию!\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username}\n"
            f"ID: {user.id}\n"
            f"Номер телефона: {phone}"
        )

    else:
        await message.answer("Чтобы зарегистрироваться, нажмите кнопку «📱 Поделиться контактом для регистрации».")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())