# Reply-клавиатура для главного меню с кнопкой "Menu główne"
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Menu główne")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Wybierz opcję z menu..."
    )