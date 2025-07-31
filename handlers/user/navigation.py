# handlers/user/navigation.py
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline.menu import main_menu_inline_kb
from keyboards.inline.order import category_selection_kb
from states.user_states import OrderStates
from database.crud import get_products
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# 🏠 Возврат в главное меню
@router.callback_query(lambda c: c.data == "to_main")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Wróciłeś do menu głównego. Wybierz opcję:",
        reply_markup=main_menu_inline_kb()
    )
    await callback.answer()


# 🔙 Назад к списку товаров
@router.callback_query(lambda c: c.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    city = data.get("city")

    products = await get_products(category, city)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{record['name']} – {record['price']} zł",
                callback_data=f"product_{record['id']}"
            )] for record in products
        ] + [[
            InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_category"),
            InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")
        ]]
    )

    await callback.message.delete()
    await callback.message.answer(
        f"📋 Produkty w kategorii: {category.capitalize()}",
        reply_markup=keyboard
    )
    await callback.answer()


# 🔙 Назад к выбору категории
@router.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)
    await callback.message.delete()
    await callback.message.answer(
        "📦 Wybierz kategorię produktów:",
        reply_markup=category_selection_kb()
    )
    await callback.answer()
