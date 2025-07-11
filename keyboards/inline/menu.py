from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🛒 Zakupy",
                callback_data="menu_zakupy"
            )],
            [InlineKeyboardButton(
                text="📦 Katalog",
                callback_data="menu_katalog"
            )],
            [InlineKeyboardButton(
                text="📖 Historia zamówień",
                callback_data="menu_historia"
            )],
            [InlineKeyboardButton(
                text="🎁 Kod promocyjny",
                callback_data="menu_bonus"
            )],
            [InlineKeyboardButton(
                text="📜 Regulamin",
                callback_data="menu_regulamin"
            )],
            [InlineKeyboardButton(
                text="💬 Pomoc",
                callback_data="menu_pomoc"
            )]
        ]
    )
