from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.types import Contact
from bot.utils.database import (
    create_coupon_with_details, get_user_coupons, use_coupon, 
    COUPON_TYPES, CONTACT_METHODS, update_coupon_status, get_pending_coupons,
    get_payment_coupons, get_coupon_by_id
)
from bot.fsm import CouponStates
from bot.config import MAIN_KB, ADMIN_IDS, LANGUAGE, bot
import json
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = Router()

# Реквизиты для оплаты 
PAYMENT_DETAILS = {
    "bank": "Сбер",
    "phone": "+7 (922) 671-78-29",  
    "name": "Елена Зубова"
}

CONTACT_METHODS = {
    "1": "Telegram",
    "2": "Телефон", 
    "3": "Только имя"
}

@router.message(F.text == "🎁 Купоны")
async def coupons_menu(message: types.Message):
    ROOT_DIR = Path(__file__).parent.parent.parent
    texts_path = ROOT_DIR / "texts" / f"{LANGUAGE}.json"
    try:
        with open(texts_path, "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        await message.answer("❌ Ошибка: файл локализации не найден.")
        return

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎫 Создать купон")],
            [types.KeyboardButton(text="📋 Мои купоны")],
            [types.KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    
    text = (
        "🎁 Подарочные купоны\n\n"
        "Хотите подарить красивую кожу близкому?\n\n"
        "1. 💎 \"Глубокое очищение\" — 3500 ₽\n"
        "2. 🔁 \"Перезагрузка кожи\" — 6000 ₽\n"
        "3. ✨ \"Жена миллионера\" — 5000 ₽\n\n"
        "Выберите действие:"
    )
    
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "🎫 Создать купон")
async def start_coupon_creation(message: types.Message, state: FSMContext):
    text = (
        "🎁 Подарочные купоны\n\n"
        "Выберите услугу:\n\n"
        "1. 💎 \"Глубокое очищение\" — 3500 ₽\n"
        "2. 🔁 \"Перезагрузка кожи\" — 6000 ₽\n"
        "3. ✨ \"Жена миллионера\" — 5000 ₽\n\n"
        "Введите номер (1, 2 или 3):"
    )
    await message.answer(text)
    await state.set_state(CouponStates.waiting_for_choice)

@router.message(CouponStates.waiting_for_choice, F.text.in_(["1", "2", "3"]))
async def choose_service(message: types.Message, state: FSMContext):
    choice = message.text
    service_data = COUPON_TYPES[choice]
    
    # ИСПРАВЛЕНО: используем "base_price" вместо "price"
    await state.update_data(
        coupon_type=choice, 
        service_name=service_data["name"], 
        base_price=service_data["base_price"]  # ← ИСПРАВЛЕНО ЗДЕСЬ
    )

    text = (
        f"{service_data['name']}\n\n"
        f"• 1 сеанс — {service_data['base_price']} ₽\n"  # ← И здесь
        f"• 3 сеанса — {int(service_data['base_price'] * 3 * 0.9)} ₽ (−10%)\n"  # ← И здесь
        f"• 5 сеансов — {int(service_data['base_price'] * 5 * 0.85)} ₽ (−15%)\n\n"  # ← И здесь
        f"👉 Экономия до {service_data['base_price'] * 5 - int(service_data['base_price'] * 5 * 0.85)} ₽\n\n"  # ← И здесь
        "Выберите количество сеансов:\n"
        "1 — Один сеанс\n"
        "2 — Три сеанса\n"
        "3 — Пять сеансов"
    )
    await message.answer(text)
    await state.set_state(CouponStates.waiting_for_sessions)

@router.message(CouponStates.waiting_for_sessions, F.text.in_(["1", "2", "3"]))
async def choose_sessions(message: types.Message, state: FSMContext):
    sessions_choice = message.text
    sessions = 1 if sessions_choice == "1" else (3 if sessions_choice == "2" else 5)
    await state.update_data(sessions=sessions)
    
    await message.answer("Введите имя получателя (например, \"Анна\"):")
    await state.set_state(CouponStates.waiting_for_recipient)

@router.message(CouponStates.waiting_for_recipient, F.text)
async def get_recipient_name(message: types.Message, state: FSMContext):
    await state.update_data(recipient=message.text)
    
    text = (
        "📞 Как связаться с получателем?\n\n"
        "1. 📲 Telegram (поделиться контактом или @username)\n"
        "2. 📞 По телефону (ввести номер)\n"
        "3. ✍️ Только имя (без контактов)\n\n"
        "Выберите 1, 2 или 3"
    )
    await message.answer(text)
    await state.set_state(CouponStates.waiting_for_contact_method)

@router.message(CouponStates.waiting_for_contact_info, F.text)
async def get_contact_info(message: types.Message, state: FSMContext):
    """Обрабатывает ввод контактной информации для варианта 'Только имя'"""
    contact_info = message.text.strip()
    
    if not contact_info:
        await message.answer("❌ Пожалуйста, введите контактную информацию.")
        return
    
    await state.update_data(contact_info=contact_info)
    await message.answer("Введите своё имя (от кого подарок):")
    await state.set_state(CouponStates.waiting_for_sender)

@router.message(CouponStates.waiting_for_contact_method, F.text.in_(["1", "2", "3"]))
async def get_contact_method(message: types.Message, state: FSMContext):
    method_choice = message.text
    contact_method = CONTACT_METHODS[method_choice]
    await state.update_data(contact_method=contact_method)
    
    if method_choice == "1":
        # Telegram вариант - предлагаем два способа
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
                [types.KeyboardButton(text="Ввести @username")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "Выберите способ:\n\n"
            "• Нажмите '📱 Поделиться контактом' или\n"
            "• Введите @username получателя",
            reply_markup=kb
        )
        # МЕНЯЕМ состояние на новое
        await state.set_state(CouponStates.waiting_for_telegram_contact)
        
    elif method_choice == "2":
        await message.answer("Введите номер телефона получателя:", 
                        reply_markup=types.ReplyKeyboardRemove())
        # МЕНЯЕМ состояние на новое  
        await state.set_state(CouponStates.waiting_for_phone_contact)
    else:
        # method_choice == "3" - Только имя
        await state.update_data(contact_info="Не указано")  # или ""
        await message.answer("Введите своё имя (от кого подарок):",
                        reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(CouponStates.waiting_for_sender)

@router.message(CouponStates.waiting_for_telegram_contact, F.contact)
async def get_contact_from_phonebook(message: types.Message, state: FSMContext):
    """Обрабатывает контакт из телефонной книжки"""
    contact = message.contact
    
    if not contact.phone_number:
        await message.answer("❌ В контакте нет номера телефона. Попробуйте другой контакт.")
        return
    
    # Формируем структурированную информацию
    contact_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
    contact_info = f"TG: +{contact.phone_number}"
    
    await state.update_data(
        contact_info=contact_info,
        recipient_phone=contact.phone_number,
        recipient_name=contact_name or "Неизвестно"
    )
    
    await message.answer(f"✅ Контакт {contact_name or 'получен'}! Введите своё имя (от кого подарок):",
                    reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CouponStates.waiting_for_sender)

@router.message(CouponStates.waiting_for_telegram_contact, F.text)
async def get_username_contact(message: types.Message, state: FSMContext):
    """Обрабатывает ввод @username"""
    username = message.text.strip()
    
    # Проверяем, нажал ли пользователь кнопку или вводит текст
    if username == "Ввести @username":
        await message.answer("Введите @username получателя (начинается с @):",
                        reply_markup=types.ReplyKeyboardRemove())
        return
    
    # Проверяем формат username
    if username.startswith('@'):
        # Убираем @ для чистоты данных
        clean_username = username[1:]
        contact_info = f"TG: @{clean_username}"
        
        await state.update_data(
            contact_info=contact_info,
            recipient_username=clean_username
        )
        
        await message.answer("Введите своё имя (от кого подарок):",
                        reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(CouponStates.waiting_for_sender)
    else:
        await message.answer("Пожалуйста, введите @username (начинается с @) или поделитесь контактом")

@router.message(CouponStates.waiting_for_phone_contact, F.text)
async def get_phone_contact(message: types.Message, state: FSMContext):
    """Обрабатывает ввод номера телефона вручную"""
    phone = message.text.strip()
    
    # Простая валидация номера телефона
    if not re.match(r'^[\d\s\-\+\(\)]{5,20}$', phone):
        await message.answer("❌ Неверный формат номера. Попробуйте еще раз.")
        return
    
    contact_info = f"Тел: {phone}"
    
    await state.update_data(
        contact_info=contact_info,
        recipient_phone=phone
    )
    
    await message.answer("Введите своё имя (от кого подарок):",
                    reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CouponStates.waiting_for_sender)

@router.message(CouponStates.waiting_for_sender, F.text)
async def finalize_coupon(message: types.Message, state: FSMContext):
    sender_name = message.text
    data = await state.get_data()
    
    # Создаем купон в базе данных
    coupon_id, price = await create_coupon_with_details(
        user_id=message.from_user.id,
        coupon_type=data["coupon_type"],
        sessions=data["sessions"],
        recipient=data["recipient"],
        contact_method=data["contact_method"],
        contact_info=data.get("contact_info", "Не указано"),
        sender=sender_name
    )
    
    # Уведомляем админа (Елену)
    admin_text = (
        f"🎁 НОВЫЙ ЗАПРОС НА КУПОН\n\n"
        f"ID: {coupon_id}\n"
        f"От: {sender_name}\n"
        f"Получатель: {data['recipient']}\n"
        f"Контакт: {data.get('contact_info', 'Не указано')}\n"
        f"Услуга: {data['service_name']}\n"
        f"Сеансов: {data['sessions']}\n"
        f"Сумма: {price} ₽\n"
        f"Статус: Ожидает подтверждения"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_coupon_{coupon_id}")],
        [types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_coupon_{coupon_id}")]
    ])
    
    try:
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, admin_text, reply_markup=kb)
            logger.info(f"Уведомление отправлено админам: {ADMIN_IDS}")
    except Exception as e:
        logger.error(f"Не удалось уведомить админов: {e}")
        print(f"Не удалось уведомить админов: {e}")
    
    # Ответ пользователю
    user_text = (
        f"✅ Запрос на купон создан!\n\n"
        f"ID купона: {coupon_id}\n"
        f"Елена скоро свяжется с вами для подтверждения.\n\n"
        f"После подтверждения вам придут реквизиты для оплаты."
    )
    
    await message.answer(user_text, reply_markup=MAIN_KB)
    await state.clear()

@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cancel_coupon_creation(message: types.Message, state: FSMContext):
    """Отменяет создание купона"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=MAIN_KB)
        return
        
    await state.clear()
    await message.answer("❌ Создание купона отменено.", reply_markup=MAIN_KB)

@router.message(F.text == "📋 Мои купоны")
async def show_my_coupons(message: types.Message):
    coupons = await get_user_coupons(message.from_user.id)
    
    if not coupons:
        await message.answer("У вас пока нет купонов.", reply_markup=MAIN_KB)
        return
    
    text = "🎫 Ваши купоны:\n\n"
    for coupon in coupons:
        # ИСПРАВЛЕНО: работаем со словарём
        text += (
            f"ID: {coupon['id']}\n"
            f"Услуга: {coupon['service']}\n"
            f"Статус: {coupon['status']}\n"
            f"Сеансов: {coupon['used']}/{coupon['sessions']}\n"
            f"Сумма: {coupon['price']} ₽\n"
            f"{'─' * 20}\n"
        )
    
    await message.answer(text, reply_markup=MAIN_KB)


# Обработчики для админа (Елены)
@router.callback_query(F.data.startswith("confirm_coupon_"))
async def confirm_coupon_admin(callback: types.CallbackQuery):
    coupon_id = callback.data.split("_")[-1]
    
    await update_coupon_status(coupon_id, "Ожидает оплаты", paid="Нет")
    
    coupon = await get_coupon_by_id(coupon_id)
    if coupon:
        user_id = coupon['user_id']
        price = coupon['price']
        
        payment_text = (
            f"✅ Ваш купон подтвержден!\n\n"
            f"ID купона: {coupon_id}\n"
            f"Для активации произведите оплату:\n\n"
            f"🏦 Банк: {PAYMENT_DETAILS['bank']}\n"
            f"📞 Номер: {PAYMENT_DETAILS['phone']}\n"  
            f"👤 Получатель: {PAYMENT_DETAILS['name']}\n"
            f"💳 Сумма: {price} ₽\n\n"  
            f"📸 После оплаты отправьте скриншот чека\n"
            f"в ЛИЧНЫЕ СООБЩЕНИЯ Елене: @holodnayaplazma_bot\n\n"
            f"После проверки купон будет активирован! ✅"
        )
        
        try:
            await bot.send_message(user_id, payment_text)
            logger.info(f"Реквизиты отправлены пользователю: {user_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить реквизиты пользователю {user_id}: {e}")
            # Добавим уведомление админу об ошибке
            await bot.send_message(ADMIN_IDS[0], f"❌ Не удалось отправить реквизиты пользователю {user_id}: {e}")
    
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Подтвержден. Ожидает оплаты.",
        reply_markup=None
    )
    await callback.answer("Купон подтвержден")

@router.callback_query(F.data.startswith("reject_coupon_"))
async def reject_coupon_admin(callback: types.CallbackQuery):
    coupon_id = callback.data.split("_")[-1]
    await update_coupon_status(coupon_id, "Отклонен")
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Отклонен."
    )
    await callback.answer("Купон отклонен")

# Обработчик для отметки использования купона
@router.message(F.text == "🎫 Отметить использование купона")
async def mark_coupon_used(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Эта команда только для администратора")
        return
    
    await message.answer("Введите ID купона для отметки использования:")
    # Здесь нужно добавить состояние для ожидания ID купона

