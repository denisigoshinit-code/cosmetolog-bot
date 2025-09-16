from aiogram import Router, F, types
from bot.utils.database import get_user_appointments, cancel_appointment, get_service_name
from bot.config import MAIN_KB, LANGUAGE
import json
from pathlib import Path

router = Router()

@router.message(F.text == "🧾 Мои записи")
async def my_appointments(message: types.Message):
    appointments = await get_user_appointments(message.from_user.id)
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return

    if not appointments:
        await message.answer("📭 У вас нет активных записей.", reply_markup=MAIN_KB)
        return

    text = "📌 Ваши активные записи:\n\n"
    kb_buttons = []
    
    for appointment in appointments:
        # ИСПРАВЛЕНО: правильный порядок - (id, date, time, service_name)
        appointment_id, date_str, time_str, service_name = appointment
        text += f"📅 {date_str} в {time_str}\n💅 {service_name}\n\n"
        # Создаем кнопку с названием услуги вместо ID
        kb_buttons.append([types.KeyboardButton(text=f"❌ Отменить: {service_name}")])

    # Добавляем главное меню
    kb_buttons.append([types.KeyboardButton(text="🏠 Главное меню")])
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=kb_buttons,
        resize_keyboard=True
    )
    
    await message.answer(text, reply_markup=kb)

@router.message(F.text.startswith("❌ Отменить: "))
async def cancel_specific_appointment(message: types.Message):
    try:
        # Извлекаем название услуги из текста кнопки
        service_name = message.text.replace("❌ Отменить: ", "").strip()
        
        # Получаем все записи пользователя
        appointments = await get_user_appointments(message.from_user.id)
        
        # Ищем запись с таким названием услуги
        appointment_to_cancel = None
        for appointment in appointments:
            # ИСПРАВЛЕНО: правильный порядок - (id, date, time, service_name)
            appointment_id, date_str, time_str, current_service_name = appointment
            if current_service_name == service_name:
                appointment_to_cancel = appointment
                break
        
        if not appointment_to_cancel:
            await message.answer("❌ Запись не найдена.", reply_markup=MAIN_KB)
            return
            
        # ИСПРАВЛЕНО: правильный порядок - (id, date, time, service_name)
        appointment_id, date_str, time_str, service_name = appointment_to_cancel
        await cancel_appointment(appointment_id, message.from_user.id)
        
        await message.answer(
            f"✅ Запись на '{service_name}' отменена.", 
            reply_markup=MAIN_KB
        )
        
    except Exception as e:
        await message.answer("❌ Не удалось отменить запись.", reply_markup=MAIN_KB)