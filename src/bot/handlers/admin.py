from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from bot.utils.database import (
    get_all_coupons, get_week_appointments, mark_coupon_paid, 
    use_coupon_session, update_schedule_date, get_pending_coupons, get_active_coupons,
    get_payment_coupons, update_coupon_status, reject_coupon, get_active_coupons, get_coupon_by_id
)
from bot.commands.db_tools import get_db_stats, export_appointments_to_csv, get_schedule_for_period
from bot.fsm import AdminStates
from bot.config import ADMIN_IDS, MAIN_KB, ADMIN_KB, COUPONS_KB, SCHEDULE_KB, LANGUAGE
import json
from pathlib import Path

router = Router()

@router.message(F.text == "/admin")
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещён")
        return
    await message.answer("🎟️ Админка", reply_markup=ADMIN_KB)

@router.message(F.text == "📅 Мои клиенты")
async def admin_clients(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    appointments = await get_week_appointments()
    if not appointments:
        await message.answer("📭 Нет записей на ближайшую неделю", reply_markup=ADMIN_KB)
        return

    text = "📅 ЗАПИСИ НА БЛИЖАЙШУЮ НЕДЕЛЮ\n\n"
    for appointment in appointments:  # ИЗМЕНЕНО: appointments теперь словарь
        text += f"📅 {appointment['date']} в {appointment['time']}\n👤 {appointment['user_name'] or 'Неизвестно'} (@{appointment['username'] or 'нет'})\n💅 {appointment['service']}\n\n"
    
    await message.answer(text, reply_markup=ADMIN_KB)

@router.message(F.text == "🎟️ Купоны")
async def admin_coupons(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🎟️ Управление купонами:", reply_markup=COUPONS_KB)

@router.message(F.text == "📋 Ожидающие купоны")
async def show_pending_coupons(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    coupons = await get_pending_coupons()
    if not coupons:
        await message.answer("Нет купонов, ожидающих подтверждения.", reply_markup=ADMIN_KB)
        return
    
    for coupon in coupons:
        # ✅ ИСПОЛЬЗУЕМ КЛЮЧИ
        text = (
            f"🎁 ЗАПРОС НА КУПОН\n\n"
            f"ID: {coupon['id']}\n"
            f"От: {coupon['sender']}\n"
            f"Для: {coupon['recipient']}\n"
            f"Контакт: {coupon['contact_info']}\n"
            f"Услуга: {coupon['service']}\n"
            f"Цена: {coupon['price']} ₽\n"
            f"Сеансов: {coupon['sessions']}\n"
            f"Статус: {coupon['status']}\n"
            f"Создан: {coupon['created_at']}"
        )
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_coupon_{coupon['id']}")],
            [types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_coupon_{coupon['id']}")]
        ])
        
        await message.answer(text, reply_markup=kb)
    
    await message.answer("Выберите действие:", reply_markup=ADMIN_KB)

@router.message(F.text == "💳 Ожидающие оплаты")
async def show_payment_coupons(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    coupons = await get_payment_coupons()
    if not coupons:
        await message.answer("Нет купонов, ожидающих оплаты.", reply_markup=COUPONS_KB)
        return
    
    for coupon in coupons:
        # ✅ ИСПОЛЬЗУЕМ КЛЮЧИ
        text = (
            f"💳 КУПОН ОЖИДАЕТ ОПЛАТЫ\n\n"
            f"ID: {coupon['id']}\n"
            f"От: {coupon['sender']}\n"
            f"Для: {coupon['recipient']}\n"
            f"Услуга: {coupon['service']}\n"
            f"Цена: {coupon['price']} ₽\n"
            f"Сеансов: {coupon['sessions']}\n"
            f"Статус: {coupon['status']}\n"
            f"Оплачено: {coupon['paid']}"
        )
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 Отметить оплату", callback_data=f"mark_paid_{coupon['id']}")]
        ])
        
        await message.answer(text, reply_markup=kb)
    
    await message.answer("Выберите действие:", reply_markup=COUPONS_KB)

# Добавляем обработчик для отметки оплаты
@router.callback_query(F.data.startswith("mark_paid_"))
async def mark_paid_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    
    coupon_id = callback.data.split("_")[2]
    await mark_coupon_paid(coupon_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Оплата отмечена. Купон активен."
    )
    await callback.answer("Купон активирован")

@router.message(F.text == "✅ Активные купоны")
async def show_active_coupons(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    coupons = await get_active_coupons()
    if not coupons:
        await message.answer("Нет активных купонов.", reply_markup=COUPONS_KB)
        return
    
    for coupon in coupons:
        # ✅ ИСПОЛЬЗУЕМ КЛЮЧИ
        text = (
            f"✅ АКТИВНЫЙ КУПОН\n\n"
            f"ID: {coupon['id']}\n"
            f"Для: {coupon['recipient']}\n"
            f"Услуга: {coupon['service']}\n"
            f"Цена: {coupon['price']} ₽\n"
            f"Сеансов: {coupon['used']} из {coupon['sessions']}\n"
            f"Статус: {coupon['status']}\n"
            f"Оплачено: {coupon['paid']}"
        )
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="✅ Отметить использование", 
                callback_data=f"use_coupon_{coupon['id']}"
            )]
        ])
        
        await message.answer(text, reply_markup=kb)
    
    await message.answer("Выберите действие:", reply_markup=COUPONS_KB)

@router.callback_query(F.data.startswith("use_coupon_"))
async def use_coupon_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    
    coupon_id = callback.data.split("_")[2]
    remaining = await use_coupon_session(coupon_id)
    
    if remaining is None:
        await callback.answer("❌ Купон не найден или все сеансы использованы")
        return
    
    # Получаем ОБНОВЛЁННЫЕ данные купона
    coupon = await get_coupon_by_id(coupon_id)
    if coupon:
        # ✅ ПРАВИЛЬНОЕ ИСПОЛЬЗОВАНИЕ СЛОВАРЯ
        text = (
            f"✅ АКТИВНЫЙ КУПОН\n\n"
            f"ID: {coupon['id']}\n"
            f"Для: {coupon['recipient']}\n"
            f"Услуга: {coupon['service']}\n"
            f"Цена: {coupon['price']} ₽\n"
            f"Сеансов: {coupon['used']} из {coupon['sessions']}\n"
            f"Статус: {coupon['status']}\n"
            f"Оплачено: {coupon['paid']}"
        )
        
        # Обновляем сообщение
        await callback.message.edit_text(text)
    
    await callback.answer(f"✅ Использование отмечено! Осталось сеансов: {remaining}")

@router.message(AdminStates.waiting_for_coupon_to_mark, F.text.startswith("GC-"))
async def mark_coupon_usage(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    coupon_id = message.text
    remaining = await use_coupon_session(coupon_id)
    
    if remaining is None:
        await message.answer("❌ Купон не найден или все сеансы использованы.", reply_markup=ADMIN_KB)
    else:
        await message.answer(f"✅ Сеанс отмечен! Осталось сеансов: {remaining}", reply_markup=ADMIN_KB)
    
    await state.clear()

@router.callback_query(F.data.startswith("pay_"))
async def mark_paid(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    coupon_id = callback.data.split("_")[1]
    await mark_coupon_paid(coupon_id)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Оплачено.")
    await callback.answer("Купон оплачен")

@router.callback_query(F.data.startswith("reject_"))
async def reject_coupon_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    coupon_id = callback.data.split("_")[1]
    await reject_coupon(coupon_id)
    await callback.message.edit_text(callback.message.text + "\n\n❌ Отклонён.")
    await callback.answer("Купон отклонён")

@router.message(F.text == "⚙️ График")
async def manage_schedule(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Выберите действие для графика:", reply_markup=SCHEDULE_KB)
    await state.set_state(AdminStates.waiting_for_schedule_action)

@router.message(AdminStates.waiting_for_schedule_action, F.text.in_(["🟩 Разрешить приём", "🟥 Заблокировать день", "⏳ Установить обед", "🌙 Ночная смена"]))
async def schedule_action(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    actions = {
        "🟩 Разрешить приём": ("Да", "09:00 – 20:00"),
        "🟥 Заблокировать день": ("Нет", "—"),
        "⏳ Установить обед": ("Да", "09:00 – 17:00 (обед 13:00–14:00)"),
        "🌙 Ночная смена": ("До 18:00", "09:00 – 17:00")
    }
    status, time_range = actions[message.text]
    await state.update_data(status=status, time_range=time_range)
    await message.answer("Введите дату (YYYY-MM-DD):")
    await state.set_state(AdminStates.waiting_for_date)

@router.message(AdminStates.waiting_for_date, F.text.len() == 10)
async def update_schedule_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    date = message.text
    data = await state.get_data()
    await update_schedule_date(date, data["status"], data["time_range"])
    await message.answer(f"✅ График на {date} обновлён.", reply_markup=ADMIN_KB)
    await state.clear()

@router.message(F.text == "📅 Показать график")
async def show_schedule(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Получаем график на ближайшие 14 дней
    from datetime import datetime, timedelta
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    schedule = await get_schedule_for_period(start_date, end_date)
    if not schedule:
        await message.answer("❌ Не удалось получить график")
        return
    
    text = "📅 ГРАФИК РАБОТЫ (14 дней):\n\n"
    for day in schedule:
        # ИСПРАВЛЕНО: правильное обращение к элементам словаря
        date_str = day['date']
        available = day['available']
        time_range = day['time_range']
        shift_type = day['shift_type']
        
        text += f"📅 {date_str}\n"
        text += f"🟢 Доступно: {available}\n"
        text += f"⏰ Время: {time_range}\n"
        text += f"👩‍💼 Смена: {shift_type}\n"
        text += "─" * 30 + "\n"
    
    await message.answer(text)

@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    stats = await get_db_stats()
    if not stats:
        await message.answer("❌ Не удалось получить статистику")
        return
    
    text = (
        f"📊 СТАТИСТИКА БАЗЫ ДАННЫХ\n\n"
        f"👥 Пользователей: {stats['users']}\n"
        f"📅 Записей: {stats['appointments']}\n"
        f"🎫 Купонов: {stats['coupons']}\n\n"
        f"📋 Последние записи:\n"
    )
    
    for appointment in stats['recent_appointments']:
        text += f"• {appointment['date']} {appointment['time']} - {appointment['service']} ({appointment['user_name']})\n"
    
    await message.answer(text)

@router.message(F.text == "📁 Экспорт в CSV")
async def export_csv(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    csv_content = await export_appointments_to_csv()
    if not csv_content:
        await message.answer("❌ Не удалось экспортировать данные")
        return
    
    # Сохраняем во временный файл
    filename = "appointments_export.csv"
    with open(filename, "w", encoding="utf-8-sig") as f:
        f.write(csv_content)
    
    # Отправляем файл правильно
    from aiogram.types import FSInputFile
    document = FSInputFile(filename)
    await message.answer_document(document, caption="📁 Экспорт записей")

@router.message(F.text == "🔙 Назад")
async def back_to_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await message.answer("🔙 Возврат в админ-панель:", reply_markup=ADMIN_KB)

@router.message(F.text == "🏠 Главное меню")
async def back_to_main(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🏠 Вы вернулись в главное меню:", reply_markup=MAIN_KB)