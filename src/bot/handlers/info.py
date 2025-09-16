# bot/handlers/info.py
from aiogram import Router, F, types
from bot.config import MAIN_KB, LANGUAGE
import logging
from pathlib import Path
import json

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📍 Где я нахожусь?")
async def show_location(message: types.Message):
    """Показывает контактную информацию и ссылки на карты."""
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return
    
    text = (
        f"{texts['location_title']}\n\n"
        f"{texts['address']}\n"
        f"{texts['phone']}\n"
        f"{texts['telegram']}\n\n"
        f"{texts['maps_yandex']}\n"
        f"{texts['maps_google']}"
    )
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True
    )
    
    try:
        await message.answer(
            text, 
            reply_markup=kb, 
            disable_web_page_preview=False
        )
        logger.info(f"User {message.from_user.id} requested location information.")
    except Exception as e:
        logger.error(f"Failed to send location info: {e}")
        await message.answer("❌ Не удалось отправить информацию. Попробуйте позже.")