from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def remove_keyboard():
    return ReplyKeyboardRemove()


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
