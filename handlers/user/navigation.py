# tg-sales-bot/handlers/user/navigation.py
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.crud import get_products, get_active_categories
from states.user_states import OrderStates

router = Router()

@router.callback_query(lambda c: c.data == "to_main")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from keyboards.inline.menu import main_menu_inline_kb
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Wróciłeś do menu głównego. Wybierz opcję:",
        reply_markup=main_menu_inline_kb()
    )
    await callback.answer()

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

# handlers/user/navigation.py
# ... остальной импорт ...

@router.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)
    data = await state.get_data()
    city = data.get("city", "")

    # ВАЖНО: берём категории именно для выбранного города
    cats = await get_active_categories(city_name=city)

    def _kb():
        rows = []
        for r in cats:
            rows.append([InlineKeyboardButton(text=f"📂 {r['name']}", callback_data=f"category_{r['code']}")])
        rows.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_city")])
        rows.append([InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.delete()
    await callback.message.answer(
        f"📦 Wybierz kategorię produktów (miasto: {city}):",
        reply_markup=_kb()
    )
    await callback.answer()
