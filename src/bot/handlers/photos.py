from aiogram import Router, F, types
from aiogram.types import InputMediaPhoto
from bot.config import MAIN_KB

router = Router()

PHOTO_1 = "AgACAgIAAxkBAAIHUmlp1DGwfzBFcMFBPrKHsTAePf_cAAL3C2sbXfBRS_LbKmhGBpIzAQADAgADeQADOAQ"
PHOTO_2 = "AgACAgIAAxkBAAIHVGlp1Dvr_YZMgiPHwidyYv0U1J8vAAL4C2sbXfBRS-Fe2Rb0vCTMAQADAgADeQADOAQ"
PHOTO_3 = "AgACAgIAAxkBAAIHVmlp1EK7B8dlYY4m-navxvmdDy59AAL5C2sbXfBRS06RAytrFmgMAQADAgADeQADOAQ"
# PHOTO_4 = "AgACAgIAAxkBAAIBQWi5BFd3dUg65k4OB7Ky3vM4d_luAALB-DEbFM_ISXNOkHCiZWXuAQADAgADeQADNgQ"
# PHOTO_5 = "AgACAgIAAxkBAAIBQmi5BFersx8vJcgYrMURtKz60__gAALC-DEbFM_ISYsMpDgAAc4zrgEAAwIAA3kAAzYE"


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