from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.database import get_available_dates

async def create_calendar(service_id: int, year: int, month: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="Пн", callback_data="ignore"),
         InlineKeyboardButton(text="Вт", callback_data="ignore"),
         InlineKeyboardButton(text="Ср", callback_data="ignore"),
         InlineKeyboardButton(text="Чт", callback_data="ignore"),
         InlineKeyboardButton(text="Пт", callback_data="ignore"),
         InlineKeyboardButton(text="Сб", callback_data="ignore"),
         InlineKeyboardButton(text="Вс", callback_data="ignore")]
    ]

    month_name = ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь")

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    inline_keyboard.append([
        InlineKeyboardButton(text="<", callback_data=f"cal_prev_{prev_year}_{prev_month}_{service_id}"),
        InlineKeyboardButton(text=f"{month_name[month-1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">", callback_data=f"cal_next_{next_year}_{next_month}_{service_id}")
    ])

    first_day = datetime(year, month, 1)
    offset = first_day.weekday()
    days_in_month = (first_day.replace(month=first_day.month % 12 + 1, day=1) - timedelta(days=1)).day

    # Получаем доступные даты
    available_dates = await get_available_dates(60)
    available_date_strs = [date['date'] for date in available_dates]

    week = []
    for _ in range(offset):
        week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    today = datetime.now().date()
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day).date()
        date_str = date_obj.strftime("%Y-%m-%d")
        
        if date_obj < today:
            week.append(InlineKeyboardButton(text="✖️", callback_data="ignore"))
        elif date_str in available_date_strs:
            week.append(InlineKeyboardButton(
                text=str(day),
                callback_data=f"cal_date_{service_id}_{date_str}"
            ))
        else:
            week.append(InlineKeyboardButton(text="✖️", callback_data="ignore"))
            
        if len(week) == 7:
            inline_keyboard.append(week)
            week = []

    if week:
        inline_keyboard.append(week + [InlineKeyboardButton(text=" ", callback_data="ignore")] * (7 - len(week)))

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)