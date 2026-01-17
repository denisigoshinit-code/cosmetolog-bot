# bot/handlers/info.py
from aiogram import Router, F, types
from aiogram.filters import StateFilter
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

    maps_yandex = texts["maps_yandex"].format(maps_yandex_url=texts["maps_yandex_url"])
    maps_google = texts["maps_google"].format(maps_google_url=texts["maps_google_url"])

    # Теперь подставляем всё в карточку
    text = texts["location_card"].format(
        location_title=texts["location_title"],
        address=texts["address"],
        phone=texts["phone"],
        telegram=texts["telegram"],
        maps_yandex=maps_yandex,
        maps_google=maps_google
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

    @router.message(F.text == "🏠 Главное меню", StateFilter("*"))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Вы вернулись в главное меню:", reply_markup=MAIN_KB)