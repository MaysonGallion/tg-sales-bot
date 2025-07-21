# tg_sales_bot/handlers/user/menu.py
from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from keyboards.inline.menu import main_menu_inline_kb
from keyboards.inline.order import city_selection_kb, category_selection_kb
from utils.logger import logger
from states.user_states import OrderStates
from database.crud import get_products, get_product_by_id

router = Router()

CITY_MAP = {
    "gdansk": "Gdańsk",
    "gdynia": "Gdynia",
    "sopot": "Sopot"
}


# 🧭 Главное меню (кроме zakupów)
@router.callback_query(lambda c: c.data.startswith("menu_") and c.data != "menu_zakupy")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: {data}")

    if data == "menu_historia":
        await callback.message.answer("📖 Tutaj będzie historia zamówień.")
    elif data == "menu_bonus":
        await callback.message.answer("🎁 Wprowadź swój kod promocyjny.")
    elif data == "menu_regulamin":
        await callback.message.answer("📜 Regulamin sklepu...")
    elif data == "menu_pomoc":
        await callback.message.answer("💬 Skontaktuj się z obsługą klienta.")

    await callback.answer()


# 🏠 Главное меню
@router.callback_query(lambda c: c.data == "to_main")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    logger.info(f"🏠 {callback.from_user.id} wrócił do menu głównego")

    await callback.message.delete()
    await callback.message.answer(
        "🏠 Wróciłeś do menu głównego. Wybierz opcję:",
        reply_markup=main_menu_inline_kb()
    )
    await callback.answer()

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


# 💳 Выбор метода оплаты
@router.callback_query(lambda c: c.data == "choose_payment")
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Gotówka na miejscu", callback_data="pay_cash")],
        [InlineKeyboardButton(text="📲 BLIK na numer", callback_data="pay_blik")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    await callback.message.delete()
    await callback.message.answer(
        "💳 <b>Wybierz metodę płatności:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


# 🔙 Назад к товарам
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


# 🔙 Назад к категориям
@router.callback_query(lambda c: c.data == "back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)

    await callback.message.delete()
    await callback.message.answer(
        "📦 Wybierz kategorię produktów:",
        reply_markup=category_selection_kb()
    )

    await callback.answer()
