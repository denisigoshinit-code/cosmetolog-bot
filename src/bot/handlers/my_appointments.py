# src/bot/handlers/my_appointments.py
from aiogram import Router, F, types
from bot.utils.database import get_user_appointments, log_button_click, log_cancellation, get_appointment_by_id, cancel_appointment
from bot.config import MAIN_KB, LANGUAGE
import json
from pathlib import Path
from bot.utils.logger import log

router = Router()


@router.message(F.text == "🧾 Мои записи")
async def my_appointments(message: types.Message):
    """
    Показывает все активные записи пользователя.
    Каждая запись — отдельное сообщение с inline-кнопкой отмены.
    """
    user_id = message.from_user.id
    appointments = await get_user_appointments(user_id)

    # Загружаем тексты
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return
    
    await log_button_click(message.from_user.id, "🧾 Мои записи")

    if not appointments:
        await message.answer("📭 У вас нет активных записей.", reply_markup=MAIN_KB)
        return

    # Отправляем каждую запись отдельно с кнопкой
    for appt in appointments:
        appointment_id, date_str, time_str, service_name = appt

        text = (
            f"📌 *Ваша запись*\n\n"
            f"📅 {date_str} в {time_str}\n"
            f"💅 {service_name}"
        )

        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="❌ Отменить эту запись",
                callback_data=f"cancel_appt_{appointment_id}"
            )]
        ])

        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    # В конце — главное меню
    await message.answer("Выберите действие:", reply_markup=MAIN_KB)


@router.callback_query(F.data.startswith("cancel_appt_"))
async def cancel_appointment_callback(callback: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку отмены записи.
    Использует ID записи для точной отмены.
    """
    try:
        appointment_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id

        success = await cancel_appointment(appointment_id, user_id)

        if success:
                # Получаем дату и время записи для лога
            appt = await get_appointment_by_id(appointment_id)
            if appt:
                scheduled_time = f"{appt['date']} {appt['time']}"
                await log_cancellation(appointment_id, user_id, scheduled_time)
            # Меняем текст и убираем кнопку
            await callback.message.edit_text(
                "✅ Запись отменена.",
                reply_markup=None
            )
            await callback.answer("Запись успешно отменена")
            log(user_id=user_id, action="appointment_cancelled", appointment_id=appointment_id)
        else:
            await callback.answer("❌ Запись не найдена", show_alert=True)
            log(user_id=user_id, action="appointment_not_found", appointment_id=appointment_id)

    except ValueError:
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        log(user_id=callback.from_user.id, action="cancel_appointment_failed", error="invalid_id_format")
    except Exception as e:
        await callback.answer("❌ Ошибка при отмене", show_alert=True)
        log(user_id=callback.from_user.id, action="cancel_appointment_failed", error=str(e))