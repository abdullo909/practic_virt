# bot_movie_pro.py
import telebot
from telebot import types
import json
import os
import time
from functools import wraps

# ==============
#  НАСТРОЙКИ
# ==============
BOT_TOKEN = "8567077313:AAFquTN6WU9GqXrgA38oOzULJfB5d4hAecM"  # можно заменить
CHANNEL_USERNAME = "myfilmzonehub"   # без @
ADMIN_ID = 6408109992                # твой Telegram ID (int)

DATA_DIR = "bot_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
PENDING_FILE = os.path.join(DATA_DIR, "pending_posts.json")

os.makedirs(DATA_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# -----------------------
#  Утилиты для JSON
# -----------------------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------
#  Инициализация данных
# -----------------------
users = load_json(USERS_FILE, {})            # ключ: str(user_id) -> info
stats = load_json(STATS_FILE, {
    "bot_starts": 0,
    "search_requests": 0,
    "posts_sent": 0,
    "checks": 0,
    "users_counted": 0
})
pending_posts = load_json(PENDING_FILE, {})  # key: str(admin_id) -> {file_id, caption, url, created_at}

# -----------------------
#  Декоратор admin_only
# -----------------------
def admin_only(func):
    @wraps(func)
    def wrapper(message):
        user_id = message.from_user.id if hasattr(message, "from_user") else message.chat.id
        if user_id != ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Доступно только админу.")
            return
        return func(message)
    return wrapper

# -----------------------
#  Проверка подписки
# -----------------------
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        # возможно, бот не админ в канале или другой сбой
        return False

# -----------------------
#  Логирование пользователей
# -----------------------
def register_user(user):
    uid = str(user.id)
    changed = False
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "date": int(time.time())
        }
        changed = True
    else:
        # обновим юзернейм/имя если изменилось
        if users[uid].get("username") != user.username or users[uid].get("first_name") != user.first_name:
            users[uid]["username"] = user.username
            users[uid]["first_name"] = user.first_name
            changed = True
    if changed:
        save_json(USERS_FILE, users)

# -----------------------
#  Клавиатура "премиум"
# -----------------------
def main_menu_markup():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🎬 Фильмы"),
        types.KeyboardButton("📺 Сериалы")
    )
    kb.add(types.KeyboardButton("🔥 Аниме"), types.KeyboardButton("🔍 Поиск"))
    return kb

# ========================
#  Хэндлер /start
# ========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    register_user(message.from_user)
    stats["bot_starts"] = stats.get("bot_starts", 0) + 1
    save_json(STATS_FILE, stats)

    # проверяем подписку
    if not is_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    # отправляем красиво
    text = (
        "🎥 <b>КиноБот</b>\n\n"
        "Добро пожаловать! Здесь удобно искать фильмы и публиковать посты в канал.\n\n"
        "Выбери раздел ниже или используй команды:\n"
        "/post — начать работу с постом (админ)\n"
        "/photo — загрузить фото для поста (админ)\n"
        "/users — список пользователей (админ)\n"
        "/stats — статистика (админ)"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_markup())

# ========================
#  Подписочное сообщение
# ========================
def send_subscribe_message(user_id):
    stats["checks"] = stats.get("checks", 0) + 1
    save_json(STATS_FILE, stats)

    btn = types.InlineKeyboardMarkup()
    btn.add(types.InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME}"))
    btn.add(types.InlineKeyboardButton("✔ Проверить подписку", callback_data="check_sub"))

    bot.send_message(user_id,
                    "🔥 Чтобы пользоваться ботом — подпишись на наш канал!\n\n"
                    "После подписки нажмите «✔ Проверить подписку».",
                    reply_markup=btn)

# ========================
#  Callback: Проверка подписки
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def on_check_sub(call):
    try:
        user_id = call.from_user.id
        if is_subscribed(user_id):
            bot.answer_callback_query(call.id, "✔ Подписка подтверждена!")
            bot.send_message(user_id, "Отлично — подписка есть! Вот главное меню:", reply_markup=main_menu_markup())
        else:
            bot.answer_callback_query(call.id, "❌ Вы всё ещё не подписаны.")
            send_subscribe_message(user_id)
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка при проверке.")

# ========================
#  Обработка меню (категории)
# ========================
@bot.message_handler(func=lambda m: m.text in ["🎬 Фильмы", "📺 Сериалы", "🔥 Аниме"])
def handle_category(message):
    if not is_subscribed(message.from_user.id):
        return send_subscribe_message(message.chat.id)

    name = message.text
    # Простейший список — можешь заменить на динамический
    if name == "🎬 Фильмы":
        items = ["Фильм: Топ 1", "Фильм: Топ 2", "Фильм: Топ 3"]
    elif name == "📺 Сериалы":
        items = ["Сериал: Топ 1", "Сериал: Топ 2", "Сериал: Топ 3"]
    else:
        items = ["Аниме: Топ 1", "Аниме: Топ 2", "Аниме: Топ 3"]

    markup = types.InlineKeyboardMarkup()
    for t in items:
        markup.add(types.InlineKeyboardButton(t, url=f"https://t.me/{CHANNEL_USERNAME}"))

    bot.send_message(message.chat.id, "Выбери для просмотра:", reply_markup=markup)

# ========================
#  Поиск (простой)
# ========================
@bot.message_handler(func=lambda m: m.text == "🔍 Поиск")
def cmd_search(message):
    if not is_subscribed(message.from_user.id):
        return send_subscribe_message(message.chat.id)

    bot.send_message(message.chat.id, "Введите название фильма / сериала для поиска:")
    bot.register_next_step_handler(message, do_search)

def do_search(message):
    query = message.text.strip()
    stats["search_requests"] = stats.get("search_requests", 0) + 1
    save_json(STATS_FILE, stats)

    # псевдо-результат
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶ Смотреть", url=f"https://t.me/{CHANNEL_USERNAME}"))
    bot.send_message(message.chat.id, f"Результаты по: <b>{query}</b>\n\nПохожие найденные:", reply_markup=markup)

# ========================
#  Admin: быстрый постинг (Вариант B)
#  команды: /photo, /caption, /url, /send
# ========================
def ensure_pending(admin_id):
    key = str(admin_id)
    if key not in pending_posts:
        pending_posts[key] = {
            "file_id": None,
            "caption": None,
            "url": None,
            "created_at": int(time.time())
        }
        save_json(PENDING_FILE, pending_posts)
    return pending_posts[key]

@bot.message_handler(commands=["photo"])
def cmd_photo(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    ensure_pending(ADMIN_ID)
    bot.send_message(message.chat.id, "📸 Отправь фото (или стикер/гиф).")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    # если админ отправил фото в контексте постинга — сохраняем
    if message.from_user.id == ADMIN_ID:
        key = str(ADMIN_ID)
        ensure_pending(ADMIN_ID)
        file_id = message.photo[-1].file_id
        pending_posts[key]["file_id"] = file_id
        pending_posts[key]["created_at"] = int(time.time())
        save_json(PENDING_FILE, pending_posts)
        bot.send_message(message.chat.id, "✔ Фото сохранено. Теперь /caption — добавить подпись.")
    else:
        # обычным пользователям можно отправлять фото, но бот не сохраняет
        bot.send_message(message.chat.id, "Спасибо за фото! Если хочешь — подпишись на канал, чтобы пользоваться ботом.")

@bot.message_handler(commands=["caption"])
def cmd_caption(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    ensure_pending(ADMIN_ID)
    bot.send_message(message.chat.id, "✏ Введи подпись/описание для поста (текст).")
    bot.register_next_step_handler(message, save_caption)

def save_caption(message):
    if message.from_user.id != ADMIN_ID:
        return
    key = str(ADMIN_ID)
    ensure_pending(ADMIN_ID)
    pending_posts[key]["caption"] = message.text
    save_json(PENDING_FILE, pending_posts)
    bot.send_message(message.chat.id, "✔ Подпись сохранена. Теперь /url — добавить ссылку кнопки.")

@bot.message_handler(commands=["url"])
def cmd_url(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    ensure_pending(ADMIN_ID)
    bot.send_message(message.chat.id, "🔗 Вставь ссылку для кнопки (например: https://t.me/yourchannel).")
    bot.register_next_step_handler(message, save_url)

def save_url(message):
    if message.from_user.id != ADMIN_ID:
        return
    key = str(ADMIN_ID)
    ensure_pending(ADMIN_ID)
    pending_posts[key]["url"] = message.text.strip()
    save_json(PENDING_FILE, pending_posts)
    bot.send_message(message.chat.id, "✔ Ссылка сохранена. Проверь всё и /send — отправить в канал.")

@bot.message_handler(commands=["checkpost"])
def cmd_checkpost(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    key = str(ADMIN_ID)
    ensure_pending(ADMIN_ID)
    p = pending_posts[key]
    text = (
        f"📌 <b>Текущий черновик</b>\n\n"
        f"Фото: {'Да' if p.get('file_id') else 'Нет'}\n"
        f"Подпись: {('Есть' if p.get('caption') else 'Нет')}\n"
        f"Ссылка: {p.get('url') or 'Нет'}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["send"])
def cmd_send(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    key = str(ADMIN_ID)
    ensure_pending(ADMIN_ID)
    p = pending_posts[key]

    if not p.get("file_id"):
        return bot.send_message(message.chat.id, "❌ Нет фото. Используй /photo и отправь фото.")
    # caption может быть пустой
    caption = p.get("caption") or ""
    url = p.get("url")

    # формируем кнопки (если есть ссылка — одна кнопка)
    markup = None
    if url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶ Смотреть", url=url))

    try:
        bot.send_photo(f"@{CHANNEL_USERNAME}", p["file_id"], caption=caption, reply_markup=markup)
        stats["posts_sent"] = stats.get("posts_sent", 0) + 1
        save_json(STATS_FILE, stats)
        # очистим черновик
        pending_posts[key] = {
            "file_id": None,
            "caption": None,
            "url": None,
            "created_at": int(time.time())
        }
        save_json(PENDING_FILE, pending_posts)
        bot.send_message(message.chat.id, "✔ Пост отправлен в канал!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при отправке: {e}\nУбедись, что бот админ канала и у канала корректный username.")

# ========================
#  Команды админа: /users и /stats
# ========================
@bot.message_handler(commands=["users"])
def cmd_users(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    # подсчёт пользователей
    users_local = load_json(USERS_FILE, {})
    cnt = len(users_local)
    # небольшой список первых 20 для просмотра
    sample = []
    for k, v in list(users_local.items())[:20]:
        uname = f"@{v.get('username')}" if v.get("username") else ""
        sample.append(f"{v.get('first_name','?')} {uname} — {v.get('id')}")
    text = f"👥 Всего пользователей: <b>{cnt}</b>\n\nПервые {len(sample)}:\n" + "\n".join(sample)
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    stats_local = load_json(STATS_FILE, {
        "bot_starts": 0,
        "search_requests": 0,
        "posts_sent": 0,
        "checks": 0
    })
    text = (
        f"📊 Статистика бота:\n\n"
        f"Запуски /start: {stats_local.get('bot_starts',0)}\n"
        f"Проверки подписки (check): {stats_local.get('checks',0)}\n"
        f"Поисковые запросы: {stats_local.get('search_requests',0)}\n"
        f"Постов отправлено: {stats_local.get('posts_sent',0)}"
    )
    bot.send_message(message.chat.id, text)

# ========================
#  Команда /post (альтернатива для админа) — запускает шаблон процесса
#  (для тех, кто хочет пройти шаги последовательно)
# ========================
@bot.message_handler(commands=["post"])
def cmd_post(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Только админ.")
    ensure_pending(ADMIN_ID)
    bot.send_message(message.chat.id,
                    "Запуск процесса публикации (быстрый режим B).\n\n"
                    "1) /photo — отправь фото для поста\n"
                    "2) /caption — добавь текст\n"
                    "3) /url — добавь кнопку (опционально)\n"
                    "4) /send — отправить в канал\n\n"
                    "Проверить черновик: /checkpost")

# ========================
#  Обработка неизвестных команд/сообщений
# ========================
@bot.message_handler(func=lambda m: True, content_types=["text", "sticker", "video", "audio", "document"])
def unknown(message):
    # регистрируем пользователя если новый
    register_user(message.from_user)
    # если пользователь не подписался — напомним
    if not is_subscribed(message.from_user.id):
        return send_subscribe_message(message.chat.id)
    # иначе — подсказать меню
    bot.send_message(message.chat.id, "Выбери в меню или используй поиск 🔍", reply_markup=main_menu_markup())

# ========================
#  Запуск
# ========================
if __name__ == "__main__":
    print("Cinema PRO bot running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
