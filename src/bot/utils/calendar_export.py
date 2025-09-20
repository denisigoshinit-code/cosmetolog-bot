# src/bot/utils/calendar_export.py
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

def create_ics_file(date_str: str, time_str: str, service: str) -> bytes:
    # Читаем часовой пояс из .env или используем по умолчанию
    tz = pytz.timezone("Asia/Yakutsk")  # Укажи нужный часовой пояс

    # Парсим дату и время
    dtstart = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dtend = dtstart + timedelta(hours=1)  # Предположим, что сеанс длится 1 час

    # Привязываем к часовому поясу
    dtstart = tz.localize(dtstart)
    dtend = tz.localize(dtend)

    # Создаём календарь
    cal = Calendar()
    cal.add('prodid', '-//BeautyByElenaBot//mxm.dk//')
    cal.add('version', '2.0')

    # Создаём событие
    event = Event()
    event.add('summary', f"Запись: {service}")
    event.add('dtstart', dtstart)
    event.add('dtend', dtend)
    event.add('dtstamp', datetime.now(tz))
    event.add('location', 'г. Свободный, ул. Управленческая, 35, студия 24б')
    event.add('description', 'Запись к косметологу Елене')

    cal.add_component(event)
    return cal.to_ical()