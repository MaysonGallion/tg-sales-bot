# tg_sales_bot/keyboards/inline/order.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def city_selection_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Gdańsk", callback_data="city_gdansk")],
        [InlineKeyboardButton(text="📍 Gdynia", callback_data="city_gdynia")],
        [InlineKeyboardButton(text="📍 Sopot", callback_data="city_sopot")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="to_main")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")],
    ])


def category_selection_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍵 Herbaty", callback_data="category_herbata")],
        [InlineKeyboardButton(text="🍬 Słodycze", callback_data="category_slodycze")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="menu_zakupy")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")],
    ])


def product_card_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Metoda płatności", callback_data="choose_payment")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])


def payment_method_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Gotówka na miejscu", callback_data="pay_cash")],
        [InlineKeyboardButton(text="📲 BLIK na numer", callback_data="pay_blik")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])


def blik_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Opłacone, przejdź dalej", callback_data="blik_paid")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])
