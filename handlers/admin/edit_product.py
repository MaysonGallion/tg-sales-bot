# tg-sales-bot/handlers/admin/edit_product.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from states.admin_states import EditProductState
from utils.access_guard import is_admin
from utils.logger import logger
from config import IMAGE_UPLOAD_PATH

from database.crud.products import (
    get_products_page, get_product_by_id,
    update_product_name, update_product_description, update_product_price,
    update_product_city, update_product_category, update_product_photo,
    set_product_active, delete_product
)

from keyboards.inline.admin import (
    admin_main_kb, admin_nav_kb, choose_city_kb, choose_category_kb,
    edit_list_kb, edit_product_menu_kb, confirm_delete_kb
)
from keyboards.inline.menu import main_menu_inline_kb

import os
import uuid

router = Router()
PAGE_SIZE = 10

async def _safe_edit_text(
    msg: types.Message,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
    disable_web_page_preview: bool = True,
):
    try:
        await msg.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "message is not modified" in s:
            try:
                await msg.edit_reply_markup(reply_markup=reply_markup)
            except Exception:
                pass
        else:
            await msg.answer(
                text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview
            )

# ===== Helpers =====

async def _render_edit_menu(callback: CallbackQuery, product_id: int, notice: str | None = None):
    product = await get_product_by_id(product_id)
    if not product:
        await _safe_edit_text(callback.message, "❌ Produkt nie znaleziony.", reply_markup=admin_main_kb())
        return

    caption = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"{(product['description'] or '')}\n\n"
        f"💰 {product['price']} zł | "
        f"📂 {product['category']} | "
        f"🏙 {product['city']} | "
        f"{'✅ aktywny' if product['active'] else '❌ ukryty'}"
    )
    if notice:
        caption = f"{notice}\n\n{caption}"

    photo_path = f".{product['photo_url']}" if product['photo_url'] else None
    kb = edit_product_menu_kb(product_id=product_id, is_active=product['active'])

    try:
        if photo_path and os.path.isfile(photo_path):
            await callback.message.delete()
            await callback.message.answer_photo(FSInputFile(photo_path), caption=caption, parse_mode="HTML", reply_markup=kb)
        else:
            await _safe_edit_text(callback.message, caption, reply_markup=kb)
    except Exception as e:
        logger.warning(f"⚠️ Failed to send product photo: {e}")
        await _safe_edit_text(callback.message, caption, reply_markup=kb)

# ===== Entry & list =====

@router.callback_query(F.data == "admin_edit_open")
async def edit_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.clear()
    await state.set_state(EditProductState.choosing_product)
    await state.update_data(page=1)
    await _send_page(callback, page=1)

@router.callback_query(EditProductState.choosing_product, F.data.startswith("admin_edit_page_"))
async def edit_page(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = int(callback.data.split("_")[-1])
    await state.update_data(page=page)
    await _send_page(callback, page=page)

async def _send_page(callback: CallbackQuery, page: int):
    products, has_next = await get_products_page(page=page, page_size=PAGE_SIZE)
    has_prev = page > 1
    if not products:
        await _safe_edit_text(callback.message, "❌ Brak produktów.", reply_markup=admin_main_kb())
        return await callback.answer()
    await _safe_edit_text(
        callback.message,
        "<b>✏️ Edycja towarów — wybierz pozycję:</b>",
        reply_markup=edit_list_kb([dict(p) for p in products], page, has_prev, has_next),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(EditProductState.choosing_product, F.data.startswith("admin_edit_select_"))
async def edit_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductState.edit_menu)
    await _render_edit_menu(callback, product_id)

# ===== Back / Cancel / Menus =====

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    data = await state.get_data()
    if cur == EditProductState.edit_menu.state:
        page = data.get("page", 1)
        await state.set_state(EditProductState.choosing_product)
        await _send_page(callback, page=page)
    elif cur in (
        EditProductState.editing_name.state,
        EditProductState.editing_description.state,
        EditProductState.editing_price.state,
        EditProductState.editing_city.state,
        EditProductState.editing_category.state,
        EditProductState.replacing_photo.state,
        EditProductState.confirm_delete.state,
    ):
        await state.set_state(EditProductState.edit_menu)
        await _render_edit_menu(callback, product_id=int(data["product_id"]))
    else:
        await state.clear()
        await _safe_edit_text(callback.message, "🏠 Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_edit_text(callback.message, "🚫 Anulowano. Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_menu_admin")
async def admin_menu_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_edit_text(callback.message, "🏠 Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_menu_user")
async def admin_menu_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_edit_text(callback.message, "🏠 Menu główne:", reply_markup=main_menu_inline_kb())
    await callback.answer()

# ===== Edit fields =====

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_name")
async def ask_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.editing_name)
    await callback.message.answer("📝 Podaj nową nazwę:", reply_markup=admin_nav_kb())

@router.message(EditProductState.editing_name)
async def set_name(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_product_name(int(data["product_id"]), message.text.strip())
    await state.set_state(EditProductState.edit_menu)
    await message.answer("✅ Nazwa zaktualizowana.", reply_markup=admin_nav_kb())
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_edit_menu(fake_cb, int(data["product_id"]))

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_desc")
async def ask_desc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.editing_description)
    await callback.message.answer("🧾 Podaj nowy opis:", reply_markup=admin_nav_kb())

@router.message(EditProductState.editing_description)
async def set_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_product_description(int(data["product_id"]), message.text.strip())
    await state.set_state(EditProductState.edit_menu)
    await message.answer("✅ Opis zaktualizowany.", reply_markup=admin_nav_kb())
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_edit_menu(fake_cb, int(data["product_id"]))

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_price")
async def ask_price(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.editing_price)
    await callback.message.answer("💰 Podaj nową cenę (np. 19.99):", reply_markup=admin_nav_kb())

@router.message(EditProductState.editing_price)
async def set_price(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        price = float(message.text.strip().replace(",", "."))
    except Exception:
        return await message.answer("❌ Nieprawidłowa cena. Spróbuj jeszcze raz.", reply_markup=admin_nav_kb())
    await update_product_price(int(data["product_id"]), price)
    await state.set_state(EditProductState.edit_menu)
    await message.answer("✅ Cena zaktualizowana.", reply_markup=admin_nav_kb())
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_edit_menu(fake_cb, int(data["product_id"]))

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_city")
async def ask_city(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.editing_city)
    await callback.message.answer("🏙 Wybierz miasto:", reply_markup=choose_city_kb())

@router.callback_query(EditProductState.editing_city, F.data.startswith("admin_city_"))
async def set_city(callback: CallbackQuery, state: FSMContext):
    city_map = {"gdansk":"Gdańsk","gdynia":"Gdynia","sopot":"Sopot","all":"Wszystkie"}
    city = city_map.get(callback.data.split("_")[2])
    if not city:
        await callback.answer("❌ Nieznane miasto")
        return
    data = await state.get_data()
    await update_product_city(int(data["product_id"]), city)
    await state.set_state(EditProductState.edit_menu)
    await _render_edit_menu(callback, int(data["product_id"]), "✅ Miasto zaktualizowane.")

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_category")
async def ask_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.editing_category)
    await callback.message.answer("📂 Wybierz kategorię:", reply_markup=choose_category_kb())

@router.callback_query(EditProductState.editing_category, F.data.startswith("admin_cat_"))
async def set_category(callback: CallbackQuery, state: FSMContext):
    cat_map = {"herbata":"herbata","slodycze":"slodycze"}
    category = cat_map.get(callback.data.split("_")[2])
    if not category:
        await callback.answer("❌ Nieznana kategoria")
        return
    data = await state.get_data()
    await update_product_category(int(data["product_id"]), category)
    await state.set_state(EditProductState.edit_menu)
    await _render_edit_menu(callback, int(data["product_id"]), "✅ Kategoria zaktualizowana.")

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_toggle")
async def toggle_active(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = await get_product_by_id(int(data["product_id"]))
    if not product:
        await _safe_edit_text(callback.message, "❌ Produkt nie znaleziony.", reply_markup=admin_main_kb())
        return await callback.answer()
    await set_product_active(int(data["product_id"]), not product["active"])
    await _render_edit_menu(callback, int(data["product_id"]), "🔁 Zmieniono status dostępności.")
    await callback.answer()

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_photo")
async def ask_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.replacing_photo)
    await callback.message.answer("🖼 Wyślij nowe zdjęcie produktu:", reply_markup=admin_nav_kb())

@router.message(EditProductState.replacing_photo)
async def set_photo(message: Message, state: FSMContext):
    if not message.photo:
        return await message.answer("❌ To nie jest zdjęcie. Wyślij prawidłowe zdjęcie.", reply_markup=admin_nav_kb())
    data = await state.get_data()
    photo = message.photo[-1]
    photo_id = str(uuid.uuid4())
    os.makedirs(IMAGE_UPLOAD_PATH, exist_ok=True)
    file_path = os.path.join(IMAGE_UPLOAD_PATH, f"{photo_id}.jpg")
    await message.bot.download(photo, destination=file_path)
    new_url = f"/images/{photo_id}.jpg"
    await update_product_photo(int(data["product_id"]), new_url)
    await state.set_state(EditProductState.edit_menu)
    await message.answer("✅ Zdjęcie zaktualizowane.", reply_markup=admin_nav_kb())
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_edit_menu(fake_cb, int(data["product_id"]))

@router.callback_query(EditProductState.edit_menu, F.data == "admin_edit_delete")
async def ask_delete(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProductState.confirm_delete)
    await _safe_edit_text(callback.message, "🗑 Czy na pewno usunąć produkt?", reply_markup=confirm_delete_kb())

@router.callback_query(EditProductState.confirm_delete, F.data == "admin_edit_delete_confirm")
async def do_delete(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await delete_product(int(data["product_id"]))
    await state.set_state(EditProductState.choosing_product)
    await _safe_edit_text(callback.message, "🗑 Produkt usunięty.", reply_markup=admin_main_kb())
    await callback.answer()
