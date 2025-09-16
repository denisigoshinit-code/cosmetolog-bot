from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from bot.utils.database import get_tomorrow_appointments, get_today_appointments 
from .schedule_manager import auto_extend_schedule
from bot.config import bot, ADMIN_IDS

from .logger import logger

scheduler = AsyncIOScheduler()

async def send_reminder_24h(user_id: int, date_str: str, time: str, service: str):  # date_str вместо date
    """Отправляет напоминание за 24 часа"""
    try:
        text = (
            f"🔔 Напоминание о записи!\n\n"
            f"Завтра в {time} у вас запись:\n"
            f"💅 {service}\n\n"
            f"Пожалуйста, подтвердите ваше присутствие 👍"
        )
        await bot.send_message(user_id, text)
        logger.info(f"REMINDER_24H_SENT - User: {user_id}, Date: {date_str}, Time: {time}")
    except Exception as e:
        logger.error(f"REMINDER_24H_FAILED - User: {user_id}, Error: {e}")

async def send_reminder_2h(user_id: int, date_str: str, time: str, service: str):  # date_str вместо date
    """Отправляет напоминание за 2 часа"""
    try:
        text = (
            f"⏰ Скоро запись!\n\n"
            f"Через 2 часа в {time}:\n"
            f"💅 {service}\n\n"
            f"Жду вас! Приходите за 10 минут 🕐"
        )
        await bot.send_message(user_id, text)
        logger.info(f"REMINDER_2H_SENT - User: {user_id}, Time: {time}")
    except Exception as e:
        logger.error(f"REMINDER_2H_FAILED - User: {user_id}, Error: {e}")

async def schedule_reminders():
    """Планирует напоминания о записях"""
    # Напоминания за 24 часа (на завтра)
    tomorrow_appointments = await get_tomorrow_appointments()
    for appointment in tomorrow_appointments:
        date_str = appointment['date']  # Получаем строку даты
        time = appointment['time']
        service = appointment['service']
        user_id = appointment['user_id']
        
        # Преобразуем строку в datetime для расчета времени напоминания
        appointment_datetime = datetime.strptime(f"{date_str} {time}", "%Y-%m-%d %H:%M")
        reminder_time = appointment_datetime - timedelta(hours=24)
        
        if reminder_time > datetime.now():
            scheduler.add_job(
                send_reminder_24h,
                DateTrigger(run_date=reminder_time),
                args=[user_id, date_str, time, service]  # Передаем строку даты
            )
    
    # Напоминания за 2 часа (на сегодня)
    today_appointments = await get_today_appointments()
    for appointment in today_appointments:
        date_str = appointment['date']  # Получаем строку даты
        time = appointment['time']
        service = appointment['service']
        user_id = appointment['user_id']
        
        appointment_datetime = datetime.strptime(f"{date_str} {time}", "%Y-%m-%d %H:%M")
        reminder_time = appointment_datetime - timedelta(hours=2)
        
        if reminder_time > datetime.now():
            scheduler.add_job(
                send_reminder_2h,
                DateTrigger(run_date=reminder_time),
                args=[user_id, date_str, time, service]  # Передаем строку даты
            )

async def notify_admin_about_booking(user_name: str, service: str, date: str, time: str):
    """Уведомляет администраторов о новой записи"""
    from bot.config import ADMIN_IDS  # Добавляем импорт
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ Новая запись!\n\n"
                f"👤 {user_name}\n"
                f"💅 {service}\n"
                f"📅 {date} в {time}\n\n"
            )
        except Exception as e:
            logger.error(f"ADMIN_NOTIFY_FAILED for {admin_id}: {e}")

def setup_scheduler():
    """Настраивает и запускает планировщик"""
    scheduler.add_job(schedule_reminders, 'interval', hours=1)  # Каждый час перепланируем
    scheduler.add_job(auto_extend_schedule, 'cron', hour=2, minute=0)
    scheduler.start()
    logger.info("📅 Планировщик напоминаний запущен")