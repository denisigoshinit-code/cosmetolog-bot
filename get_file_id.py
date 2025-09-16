 # get_file_id.py
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram import F
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Укажите ваш токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.command("start"))
async def cmd_start(message: Message):
    await message.answer("Бот запущен. Отправьте фото, чтобы получить file_id.")

@dp.message(F.photo)
async def get_photo_id(message: Message):
    # Самое большое фото (последнее в списке)
    photo = message.photo[-1]
    file_id = photo.file_id
    file_size = photo.file_size
    width = photo.width
    height = photo.height

    logger.info(f"✅ file_id найден: {file_id}")
    logger.info(f"Размер: {width}x{height}, вес: {file_size} байт")

    await message.reply(
        f"📸 Фото получено!\n\n"
        f"<code>file_id = '{file_id}'</code>\n\n"
        f"Скопируйте его и вставьте в код бота.",
        parse_mode="HTML"
    )

async def main():
    logger.info("Бот запущен. Отправьте фото в чат с ботом...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Выход...")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())