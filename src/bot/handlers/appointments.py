from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from bot.utils.calendar_export import create_ics_file
from bot.utils.calendar import create_calendar
from bot.utils.database import (
    get_services, is_time_available, create_appointment, 
    get_service_name, get_user_appointments, cancel_appointment,
    get_available_time_slots, log_button_click, is_date_available, add_user
)
from bot.utils.reminders import notify_admin_about_booking
from bot.fsm import Appointment
from bot.config import MAIN_KB, LANGUAGE, ADMIN_IDS
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "📅 Записаться")
async def start_appointment(message: types.Message):
    # Добавляем пользователя в базу
    await log_button_click(message.from_user.id, "📅 Записаться")
    await add_user(
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.username
    )
    
    services = await get_services()
    if not services:
        await message.answer("Нет доступных услуг.")
        return

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=name, callback_data=f"serv_{id}")]
        for id, name, _, _ in services
    ])
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return
        
    await message.answer(texts["select_service"], reply_markup=kb)

@router.callback_query(F.data == "open_appointment")
async def open_appointment(callback: types.CallbackQuery):
    await callback.answer()
    await start_appointment(callback.message)

@router.callback_query(F.data.startswith("serv_"))
async def select_service(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    service_id = int(callback.data.split("_")[1])
    now = datetime.now()
    kb = await create_calendar(service_id, now.year, now.month)
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await callback.message.answer("❌ Ошибка: файл локализации не найден.")
        return
        
    await callback.message.answer(texts["select_date"], reply_markup=kb)
    await state.update_data(service_id=service_id)

@router.callback_query(F.data.startswith("cal_date_"))
async def select_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    service_id = int(parts[2])
    date_str = parts[3]

    # Сохраняем дату и service_id
    await state.update_data(service_id=service_id, date=date_str)

    if not await is_date_available(date_str):
        await callback.message.answer("❌ В этот день я не принимаю клиентов.")
        return

    all_slots = await get_available_time_slots(date_str)
    if not all_slots:
        await callback.message.answer("❌ В этот день нет доступного времени.")
        return

    # --- НОВАЯ ЛОГИКА: Фильтрация по времени ---
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()

    available_buttons = []
    
    for time_slot in all_slots:
        # Проверяем, свободно ли время
        is_free = await is_time_available(date_str, time_slot)
        
        if selected_date == today:
            # Если выбран сегодняшний день, проверяем, что время ещё не прошло
            hour, minute = map(int, time_slot.split(":"))
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            
            # Считаем, что запись возможна за 1 час до времени
            time_ok = (hour > current_hour + 1) or \
                     (hour == current_hour + 1 and minute >= current_minute) or \
                     (hour == current_hour and minute > current_minute)
            
            if is_free and time_ok:
                available_buttons.append([types.InlineKeyboardButton(
                    text=time_slot, 
                    callback_data=f"time_{time_slot}"
                )])
            else:
                status = " (недоступно)" if not time_ok else " (занято)"
                available_buttons.append([types.InlineKeyboardButton(
                    text=f"{time_slot}{status}", 
                    callback_data="ignore"
                )])
        else:
            # Для будущих дней — обычная логика
            if is_free:
                available_buttons.append([types.InlineKeyboardButton(
                    text=time_slot, 
                    callback_data=f"time_{time_slot}"
                )])
            else:
                available_buttons.append([types.InlineKeyboardButton(
                    text=f"{time_slot} (занято)", 
                    callback_data="ignore"
                )])

    kb = types.InlineKeyboardMarkup(inline_keyboard=available_buttons)
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await callback.message.answer("❌ Ошибка: файл локализации не найден.")
        return
        
    await callback.message.answer(
        texts["select_time"].format(date=date_str),
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    time_str = callback.data.split("_")[1]
    data = await state.get_data()

    if "date" not in data:
        await callback.message.answer("❌ Произошла ошибка. Начните запись заново.")
        await state.clear()
        return

    date_str = data["date"]
    service_id = data["service_id"]

    if not await is_time_available(date_str, time_str):
        ROOT_DIR = Path(__file__).parent.parent.parent
        texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
        try:
            with open(texts_path, "r", encoding="utf-8") as f:
                texts = json.load(f)
        except FileNotFoundError:
            await callback.message.answer("❌ Ошибка: файл локализации не найден.")
            return
        await callback.message.answer(texts["time_taken"])
        return

    # ✅ ПОЛУЧАЕМ ИМЯ УСЛУГИ ЗДЕСЬ (до format!)
    service_name = await get_service_name(service_id)
    
    await state.update_data(time=time_str)
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await callback.message.answer("❌ Ошибка: файл локализации не найден.")
        return
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
        [types.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])
    
    # ✅ ПЕРЕДАЁМ service_name в format()
    await callback.message.answer(
        texts["confirm_prompt"].format(date=date_str, time=time_str, service=service_name),
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Appointment.waiting_for_confirmation)

@router.callback_query(F.data == "confirm", Appointment.waiting_for_confirmation)
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Подтверждаю...")
    data = await state.get_data()
    user_id = callback.from_user.id
    service_id = data["service_id"]
    date_str = data["date"]
    time_str = data["time"]

    if not await is_time_available(date_str, time_str):
        await callback.message.edit_text("⚠️ Время уже занято.")
        await state.clear()
        return

    # Создаем запись
    await create_appointment(user_id, service_id, date_str, time_str)
    service_name = await get_service_name(service_id)

    # Уведомляем админа
    try:
        await notify_admin_about_booking(
            callback.from_user.first_name,
            service_name,
            date_str,
            time_str
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить админа: {e}")

    # Загружаем тексты
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await callback.message.edit_text("❌ Ошибка: файл локализации не найден.", reply_markup=None)
        await state.clear()
        return

    # 1. Подтверждение записи
    await callback.message.edit_text(
        texts["confirmed"].format(date=date_str, time=time_str, service=service_name),
        parse_mode="Markdown",
        reply_markup=None
    )

    # 2. Сообщение с информацией
    await callback.message.answer(
        texts["after_booking_message"],
        reply_markup=MAIN_KB
    )

    # 3. Карточка с адресом и картами
    maps_yandex = texts["maps_yandex"].format(maps_yandex_url=texts["maps_yandex_url"])
    maps_google = texts["maps_google"].format(maps_google_url=texts["maps_google_url"])

    location_text = texts["location_card"].format(
        location_title=texts["location_title"],
        address=texts["address"],
        phone=texts["phone"],
        telegram=texts["telegram"],
        maps_yandex=maps_yandex,
        maps_google=maps_google
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧭 Проложить маршрут (Яндекс)", url=texts["maps_yandex_url"])],
        [InlineKeyboardButton(text="📌 Проложить маршрут (Google)", url=texts["maps_google_url"])]
    ])
    await callback.message.answer(location_text, reply_markup=kb, disable_web_page_preview=False)

    # 4. Файл .ics — добавить в календарь
    from io import BytesIO
    from aiogram.types import BufferedInputFile

    ics_data = create_ics_file(date_str, time_str, service_name)
    buffer = BytesIO(ics_data)
    buffer.name = "appointment.ics"

    document = BufferedInputFile(buffer.getvalue(), filename="appointment.ics")
    await callback.message.answer_document(document, caption=texts["calendar_ics"], parse_mode="Markdown")

    await state.clear()

@router.callback_query(F.data == "cancel", Appointment.waiting_for_confirmation)
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Отменено")
    
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await callback.message.edit_text("❌ Ошибка: файл локализации не найден.", reply_markup=None)
        await state.clear()
        return
        
    await callback.message.edit_text(texts["cancelled"], reply_markup=None)
    await callback.message.answer("Выберите действие:", reply_markup=MAIN_KB)
    await state.clear()

@router.callback_query(F.data.startswith("cal_prev_"))
async def prev_month(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    year = int(parts[2])
    month = int(parts[3])
    service_id = int(parts[4])
    kb = await create_calendar(service_id, year, month)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("cal_next_"))
async def next_month(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    year = int(parts[2])
    month = int(parts[3])
    service_id = int(parts[4])
    kb = await create_calendar(service_id, year, month)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.message(F.text == "🏠 Главное меню", StateFilter("*"))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Вы вернулись в главное меню:", reply_markup=MAIN_KB)