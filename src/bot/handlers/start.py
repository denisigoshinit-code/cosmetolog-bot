# bot/handlers/start.py
from aiogram import Router, F, types
from aiogram.filters import Command
from bot.config import MAIN_KB, LANGUAGE
from bot.utils.database import add_user  
import json
from pathlib import Path

router = Router()

PHOTO_START = "AgACAgIAAxkBAAIBPmi5A7yG-MLs5c0xHIBtjOb74oWsAAK--DEbFM_ISbyJFS5JLulWAQADAgADeAADNgQ"

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Сохраняем пользователя в БД через новую функцию
    await add_user(
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.username
    )
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return

    await message.answer_photo(
        photo=PHOTO_START,
        caption=texts["start"],
        reply_markup=MAIN_KB
    )
@router.message(F.photo)
async def get_photo_id(message: types.Message):
    photo = message.photo[-1]
    file_id = photo.file_id
    await message.reply(f"📸 Ваш новый file_id:\n\n<code>{file_id}</code>", parse_mode="HTML")

    