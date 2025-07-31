# handlers/user/catalog.py
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from utils.constants import CITY_MAP
from keyboards.inline.order import city_selection_kb, category_selection_kb
from database.crud import get_products, get_product_by_id
from states.user_states import OrderStates
from utils.logger import logger

router = Router()


# 🛒 Zakupy — выбор города
@router.callback_query(lambda c: c.data == "menu_zakupy")
async def zakupy_step_1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_city)
    await state.update_data(mode="zakupy")

    logger.info(f"🛒 {callback.from_user.id} rozpoczął zakupy (wybór miasta)")

    await callback.message.edit_text(
        "🗺️ Wybierz miasto dostawy:",
        reply_markup=city_selection_kb()
    )
    await callback.answer()


# 📍 Выбор города → категория
@router.callback_query(lambda c: c.data.startswith("city_"))
async def handle_city_selection(callback: CallbackQuery, state: FSMContext):
    city_key = callback.data.split("_")[1].lower()
    city = CITY_MAP.get(city_key)

    await state.update_data(city=city)
    await state.set_state(OrderStates.choosing_category)

    logger.info(f"📍 {callback.from_user.id} wybrał miasto: {city}")

    await callback.message.edit_text(
        f"📦 Wybrałeś miasto: {city}\nTeraz wybierz kategorię:",
        reply_markup=category_selection_kb()
    )
    await callback.answer()


# 📂 Выбор категории → список товаров
@router.callback_query(lambda c: c.data.startswith("category_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    data = await state.get_data()
    city = data.get("city")

    await state.update_data(category=category)

    products = await get_products(category, city)

    if not products:
        await callback.message.edit_text("❌ Brak produktów w tej kategorii.")
        return await callback.answer()

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

    await callback.message.edit_text(
        f"📋 Produkty w kategorii: {category.capitalize()}",
        reply_markup=keyboard
    )
    await callback.answer()


# 🛍️ Карточка товара
@router.callback_query(lambda c: c.data.startswith("product_"))
async def handle_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = await get_product_by_id(product_id)

    if not product:
        await callback.message.edit_text("❌ Produkt nie został znaleziony.")
        return await callback.answer()

    await state.update_data(product_id=product_id)

    photo_path = f".{product['photo_url']}"
    photo = FSInputFile(photo_path)

    text = (
        f"🛍️ <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Cena: {product['price']} zł"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Metoda płatności", callback_data="choose_payment")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()
