import asyncio
import logging
from aiogram import Dispatcher
from bot.handlers.start import router as start_router
from bot.handlers.services import router as services_router
from bot.handlers.photos import router as photos_router
from bot.handlers.appointments import router as appointments_router
from bot.handlers.admin import router as admin_router
from bot.handlers.my_appointments import router as my_appointments_router
from bot.handlers.coupons import router as coupons_router
from bot.handlers.info import router as info_router
from bot.utils.database import init_db
from bot.utils.reminders import setup_scheduler, schedule_reminders 
from bot.config import bot, storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализируем базу данных
    await init_db()
    
    # Создаем диспетчер
    dp = Dispatcher(storage=storage)
    
    # Подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(services_router)
    dp.include_router(photos_router)
    dp.include_router(appointments_router)
    dp.include_router(admin_router)
    dp.include_router(my_appointments_router)
    dp.include_router(coupons_router)
    dp.include_router(info_router)
    
    # Запускаем планировщик напоминаний
    setup_scheduler()
    # ✅ Правильно: стартуем первое планирование НЕ блокируя запуск бота
    asyncio.create_task(schedule_reminders())
    
    logger.info("🌸 Бот для косметолога запущен с напоминаниями...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())