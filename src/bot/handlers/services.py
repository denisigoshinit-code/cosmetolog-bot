from aiogram import Router, F, types
from bot.utils.database import get_services, log_button_click
from bot.config import MAIN_KB, LANGUAGE
import json
from pathlib import Path

router = Router()

@router.message(F.text == "📋 Услуги")
async def show_services(message: types.Message):
    services = await get_services()
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return

    await log_button_click(message.from_user.id, "📋 Услуги")

    if not services:
        await message.answer(texts["no_services"])
        return

    text = f"**{texts['services_title']}**\n\n"
    for name, price, desc in [(s[1], s[2], s[3]) for s in services]:
        price_text = f"{price:,.0f} руб." if price > 0 else "Цена по запросу"
        text += f"**{name}**\nЦена: {price_text}\n"
        if desc:
            text += f"Описание: {desc}\n"
        text += "\n"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Записаться", callback_data="open_appointment")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")