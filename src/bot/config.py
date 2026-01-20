import os
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
LANGUAGE = os.getenv("LANGUAGE", "ru")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()

# Главная клавиатура
MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Услуги"), KeyboardButton(text="📸 Фото")],
        [KeyboardButton(text="📅 Записаться"), KeyboardButton(text="🧾 Мои записи")],
        [KeyboardButton(text="📍 Где я нахожусь?"), KeyboardButton(text="🎁 Купоны")]
    ],
    resize_keyboard=True
)

# Админская клавиатура
ADMIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Мои клиенты"), KeyboardButton(text="🎟️ Купоны")],
        [KeyboardButton(text="⚙️ График"), KeyboardButton(text="📅 Показать график")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📁 Экспорт в CSV")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)

# Клавиатура для управления купонами 
COUPONS_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Ожидающие купоны")],
        [KeyboardButton(text="💳 Ожидающие оплаты")],
        [KeyboardButton(text="✅ Активные купоны")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Клавиатура для управления графиком 
SCHEDULE_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟩 Разрешить приём"), KeyboardButton(text="🟥 Заблокировать день")],
        [KeyboardButton(text="⏳ Установить обед"), KeyboardButton(text="🌙 Ночная смена")],
        [KeyboardButton(text="🔒 Блокировать слот"), KeyboardButton(text="🔓 Разблокировать слот")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)