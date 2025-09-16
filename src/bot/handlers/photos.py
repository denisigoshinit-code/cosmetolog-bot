from aiogram import Router, F, types
from aiogram.types import InputMediaPhoto
from bot.config import MAIN_KB

router = Router()

PHOTO_1 = "AgACAgIAAxkBAAMFaMn3Ca2rAgJoo4O9cDvva9SnAAE5AAIU_DEb0WtRSvITYpZzZyQEAQADAgADeQADNgQ"
PHOTO_2 = "AgACAgIAAxkBAAMHaMn3WWcFH2OhNIIpAUy7zYs2nKMAAhr8MRvRa1FKsPrSkiIAAVK2AQADAgADeQADNgQ"
PHOTO_3 = "AgACAgIAAxkBAAMJaMn3f-X9e7T9ebEcZE50ylIMQoUAAhv8MRvRa1FKLccIwM1N1y0BAAMCAAN5AAM2BA"
PHOTO_4 = "AgACAgIAAxkBAAMLaMn3mvt-ObLdKRq2UxXs5zTj1tQAAhz8MRvRa1FKaggCfuMlIXoBAAMCAAN5AAM2BA"
PHOTO_5 = "AgACAgIAAxkBAAMNaMn3ql-g6R4ESOxoA0qkphedhnYAAh38MRvRa1FKddjPDzvBgg4BAAMCAAN5AAM2BA"



@router.message(F.text == "📸 До/после")
async def show_before_after(message: types.Message):
    media = [
        InputMediaPhoto(media=PHOTO_1),
        InputMediaPhoto(media=PHOTO_2),
        InputMediaPhoto(media=PHOTO_3),
        InputMediaPhoto(media=PHOTO_4),
        InputMediaPhoto(media=PHOTO_5),
    ]
    await message.answer_media_group(media)
    await message.answer("Хотите такой же результат?", reply_markup=MAIN_KB)