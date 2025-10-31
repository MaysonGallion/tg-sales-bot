# tg-sales-bot/handlers/user/catalog.py
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext

from database.crud import (
    get_products,
    get_product_by_id,
    get_user_active_promo,
    promo_applicable_for,
    apply_discount,
    get_active_cities,       # теперь из БД → [{id,name}]
    get_active_categories,   # теперь из БД → [{code,name}]
)
from states.user_states import OrderStates
from utils.logger import logger

router = Router()

# 🛒 Zakupy — выбор города (динамически из БД)
def _city_menu_with_discounts(active_promo, cities_rows) -> InlineKeyboardMarkup:
    def label(title: str) -> str:
        if active_promo:
            if active_promo["scope"] == "global" or (
                active_promo["scope"] == "city" and active_promo.get("city") == title
            ):
                if active_promo["type"] == "percent":
                    return f"{title} (−{active_promo['value']:.0f}%)"
                else:
                    return f"{title} (−{active_promo['value']:.2f})"
        return title

    rows = []
    for r in cities_rows:
        rows.append([InlineKeyboardButton(text=label(r["name"]), callback_data=f"city_{r['id']}")])

    rows.append([InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(lambda c: c.data == "back_to_city")
async def back_to_city(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_city)
    active_promo = await get_user_active_promo(callback.from_user.id)
    cities = await get_active_cities()
    await callback.message.edit_text(
        "🗺️ Wybierz miasto dostawy:",
        reply_markup=_city_menu_with_discounts(active_promo, cities)
    )
    await callback.answer()

# 📂 Выбор категории (динамически из БД)
def _category_menu_with_discounts(active_promo, city_title: str, categories_rows) -> InlineKeyboardMarkup:
    def label(row) -> str:
        title = row["name"]   # важно: в БД колонка name
        code = row["code"]
        if active_promo and promo_applicable_for(code, city_title, active_promo):
            if active_promo["type"] == "percent":
                return f"{title} (−{active_promo['value']:.0f}%)"
            else:
                return f"{title} (−{active_promo['value']:.2f})"
        return title

    rows = []
    for r in categories_rows:
        rows.append([InlineKeyboardButton(text=label(r), callback_data=f"category_{r['code']}")])
    rows.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_city")])
    rows.append([InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(lambda c: c.data == "menu_zakupy")
async def zakupy_step_1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_city)
    await state.update_data(mode="zakupy")
    logger.info(f"🛒 {callback.from_user.id} rozpoczął zakupy (wybór miasta)")

    active_promo = await get_user_active_promo(callback.from_user.id)
    cities = await get_active_cities()
    await callback.message.edit_text(
        "🗺️ Wybierz miasto dostawy:",
        reply_markup=_city_menu_with_discounts(active_promo, cities)
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("city_"))
async def handle_city_selection(callback: CallbackQuery, state: FSMContext):
    city_id = callback.data.split("_")[1]
    cities = await get_active_cities()
    row = next((r for r in cities if str(r["id"]) == city_id), None)
    if not row:
        await callback.answer("❌ Miasto nieaktywne.")
        return
    city = row["name"]

    await state.update_data(city=city)
    await state.set_state(OrderStates.choosing_category)

    logger.info(f"📍 {callback.from_user.id} wybrał miasto: {city}")

    active_promo = await get_user_active_promo(callback.from_user.id)
    # ВАЖНО: теперь категории фильтруем по городу
    categories = await get_active_categories(city_name=city)

    if not categories:
        await callback.message.edit_text(
            f"📦 Wybrałeś miasto: {city}\n"
            f"❌ Brak dostępnych kategorii w tym mieście.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_city")],
                [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")],
            ])
        )
        return await callback.answer()

    await callback.message.edit_text(
        f"📦 Wybrałeś miasto: {city}\nTeraz wybierz kategorię:",
        reply_markup=_category_menu_with_discounts(active_promo, city, categories)
    )
    await callback.answer()

# 📦 Категория → список товаров
@router.callback_query(lambda c: c.data.startswith("category_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1]  # КОД категории
    data = await state.get_data()
    city = data.get("city")

    await state.update_data(category=category)

    products = await get_products(category, city)
    if not products:
        await callback.message.edit_text(
            "❌ Brak produktów w tej kategorii.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_category")],
                [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
            ])
        )
        return await callback.answer()

    user_id = callback.from_user.id
    active_promo = await get_user_active_promo(user_id)

    def _price_line(row) -> str:
        base = float(row["price"])
        if active_promo and promo_applicable_for(category, city, active_promo):
            final, _ = apply_discount(base, active_promo)
            if active_promo["type"] == "percent":
                return f"{base:.2f}→{final:.2f} zł (-{active_promo['value']:.0f}%)"
            else:
                return f"{base:.2f}→{final:.2f} zł (-{active_promo['value']:.2f})"
        return f"{base:.2f} zł"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{record['name']} – {_price_line(record)}",
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

    data = await state.get_data()
    city = data.get("city", "")
    category = data.get("category", "")

    price = float(product['price'])
    price_txt = f"{price:.2f} zł"
    active_promo = await get_user_active_promo(callback.from_user.id)
    discount_note = ""

    if active_promo and promo_applicable_for(category, city, active_promo):
        final_price, _ = apply_discount(price, active_promo)
        price_txt = f"<s>{price:.2f} zł</s> ➝ <b>{final_price:.2f} zł</b>"
        if active_promo["type"] == "percent":
            discount_note = f"\n🎟️ Kod: <b>{active_promo['code']}</b> (−{active_promo['value']:.0f}%)"
        else:
            discount_note = f"\n🎟️ Kod: <b>{active_promo['code']}</b> (−{active_promo['value']:.2f} zł)"

    text = (
        f"🛍️ <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Cena: {price_txt}{discount_note}"
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
