from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.admin_states import AddProductState
from database.crud.products import add_product
from database.crud import get_active_categories, get_active_cities_for_products
from keyboards.inline.admin import admin_main_kb, cancel_kb
from utils.access_guard import is_admin
from config import IMAGE_UPLOAD_PATH
from aiogram.exceptions import TelegramBadRequest

import os
import uuid

router = Router()

# ───────────────────────────────────────
# безопасная замена содержимого сообщения
# ───────────────────────────────────────
async def _safe_replace_message(msg, text: str, reply_markup=None, parse_mode: str | None = "HTML"):
    """
    Пытаемся:
      1) edit_text (для обычных сообщений)
      2) edit_caption (для сообщений с фото)
      3) если не вышло — удаляем сообщение и шлём новое с текстом
    """
    try:
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except TelegramBadRequest as e:
        # если пытались редактировать caption-сообщение
        s = str(e).lower()
        if "no text in the message to edit" in s or "message is not modified" in s:
            try:
                await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
                return
            except Exception:
                pass
    except Exception:
        pass

    # на крайний случай — удаляем и шлём новое
    try:
        await msg.delete()
    except Exception:
        pass
    await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


# ───────────────────────────────────────
# КНОПКИ: ГОРОДА
# ───────────────────────────────────────
def _cities_kb(rows):
    kb = []
    for r in rows:
        kb.append([InlineKeyboardButton(text=f"📍 {r['name']}", callback_data=f"admin_city_{r['id']}")])
    # Можно оставить «Wszystkie miasta» при желании:
    # kb.append([InlineKeyboardButton(text="🌍 Wszystkie miasta", callback_data="admin_city_all")])
    kb += cancel_kb().inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ───────────────────────────────────────
# КНОПКИ: КАТЕГОРИИ (по КОДУ)
# ───────────────────────────────────────
def _categories_kb(cats) -> InlineKeyboardMarkup:
    """
    cats — [{'code': 'herbata', 'name': 'Herbaty'}, ...]
    """
    kb = []
    for r in cats:
        code = r.get("code")
        title = r.get("name", code)
        kb.append([InlineKeyboardButton(text=f"📂 {title}", callback_data=f"admin_catcode_{code}")])
    # НЕ добавляем свой «Wstecz», чтобы не дублировать — берём из cancel_kb()
    kb += cancel_kb().inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ───────────────────────────────────────
# СТАРТ
# ───────────────────────────────────────
@router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.clear()
    await state.set_state(AddProductState.waiting_for_name)
    await _safe_replace_message(callback.message, "✏️ Podaj nazwę nowego towaru:", reply_markup=cancel_kb())
    await callback.answer()


# ───────────────────────────────────────
# ШАГИ ВВОДА
# ───────────────────────────────────────
@router.message(AddProductState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=(message.text or "").strip())
    await state.set_state(AddProductState.waiting_for_description)
    await message.answer("📄 Podaj opis produktu:", reply_markup=cancel_kb())


@router.message(AddProductState.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AddProductState.waiting_for_photo)
    await message.answer("🖼️ Wyślij zdjęcie produktu:", reply_markup=cancel_kb())


@router.message(AddProductState.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    if not message.photo:
        return await message.answer("❌ To nie jest zdjęcie. Wyślij prawidłowe zdjęcie.", reply_markup=cancel_kb())
    photo = message.photo[-1]
    photo_id = str(uuid.uuid4())
    os.makedirs(IMAGE_UPLOAD_PATH, exist_ok=True)
    file_path = os.path.join(IMAGE_UPLOAD_PATH, f"{photo_id}.jpg")
    await message.bot.download(photo, destination=file_path)
    relative_path = f"/images/{photo_id}.jpg"
    await state.update_data(photo_url=relative_path)
    await state.set_state(AddProductState.waiting_for_price)
    await message.answer("💰 Podaj cenę (liczba, np. 15.99):", reply_markup=cancel_kb())


@router.message(AddProductState.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float((message.text or "").strip().replace(",", "."))
    except ValueError:
        return await message.answer("❌ Podaj prawidłową cenę (np. 19.99)", reply_markup=cancel_kb())
    await state.update_data(price=price)

    # ВАЖНО: показываем только те города, где есть хотя бы одна активная категория, привязанная к городу
    rows = await get_active_cities_for_products()
    await state.set_state(AddProductState.waiting_for_city)
    await message.answer("🏙️ Wybierz miasto dla tego produktu:", reply_markup=_cities_kb(rows))


@router.message(AddProductState.waiting_for_city)
async def block_manual_city_entry(message: Message):
    await message.answer("❌ Wybierz miasto z przycisków poniżej.")


@router.callback_query(F.data == "admin_city_back")
async def go_back_to_cities(callback: CallbackQuery, state: FSMContext):
    rows = await get_active_cities_for_products()
    await state.set_state(AddProductState.waiting_for_city)
    await _safe_replace_message(callback.message, "🏙️ Wybierz miasto dla tego produktu:", reply_markup=_cities_kb(rows))
    await callback.answer()


@router.callback_query(AddProductState.waiting_for_city, F.data.startswith("admin_city_"))
async def process_city_choice(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[2]
    # «all» можно поддерживать, если нужно. Сейчас убрали кнопку «all».
    if key == "all":
        await state.update_data(city="Wszystkie")
        cats = await get_active_categories()
    else:
        rows = await get_active_cities_for_products()
        name = next((r["name"] for r in rows if str(r["id"]) == key), None)
        if not name:
            await callback.answer("❌ Nieznane lub niedostępne miasto")
            return
        await state.update_data(city=name)
        cats = await get_active_categories(city_name=name)

    await state.set_state(AddProductState.waiting_for_category)
    await _safe_replace_message(callback.message, "📂 Wybierz kategorię:", reply_markup=_categories_kb(cats))
    await callback.answer()


@router.message(AddProductState.waiting_for_category)
async def block_manual_category_entry(message: Message):
    await message.answer("❌ Wybierz kategorię z przycisków poniżej.")


@router.callback_query(AddProductState.waiting_for_category, F.data.startswith("admin_catcode_"))
async def process_category_choice_code(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("admin_catcode_", "", 1)
    await state.update_data(category=code)
    await state.set_state(AddProductState.confirmation)

    data = await state.get_data()
    cats = await get_active_categories()
    row = next((r for r in cats if r["code"] == code), {"name": code})

    text = (
        f"<b>📦 Podsumowanie produktu:</b>\n"
        f"📛 Nazwa: {data['name']}\n"
        f"📄 Opis: {data['description']}\n"
        f"💰 Cena: {data['price']} zł\n"
        f"🏙️ Miasto: {data['city']}\n"
        f"📂 Kategoria: {row.get('name')} ({code})\n\n"
        f"Czy dodać produkt do bazy danych?"
    )
    photo_path = "." + data['photo_url']
    photo = FSInputFile(photo_path)

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tak", callback_data="admin_confirm_yes")],
        [InlineKeyboardButton(text="❌ Nie", callback_data="admin_confirm_no")]
    ])

    await callback.message.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=confirm_kb)
    await callback.answer()


# ───────────────────────────────────────
# ПОДТВЕРЖДЕНИЕ / ОТМЕНА
# ───────────────────────────────────────
@router.message(AddProductState.confirmation)
async def block_manual_confirmation(message: Message):
    await message.answer("❌ Potwierdź przyciskiem poniżej.")


@router.callback_query(AddProductState.confirmation, F.data == "admin_confirm_yes")
async def confirm_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await add_product(**data)
    await state.clear()
    await _safe_replace_message(callback.message, "✅ Produkt został dodany do bazy danych.", reply_markup=admin_main_kb())
    await callback.answer()


@router.callback_query(AddProductState.confirmation, F.data == "admin_confirm_no")
async def cancel_product_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_replace_message(callback.message, "❌ Anulowano dodawanie produktu.", reply_markup=admin_main_kb())
    await callback.answer()


# Глобальная отмена/выход (на любом шаге)
@router.callback_query(F.data == "admin_cancel")
async def cancel_any_step(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_replace_message(callback.message, "🚫 Anulowano. Wróciłeś do menu administratora.", reply_markup=admin_main_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_replace_message(callback.message, "🔄 Zrestartowano. Wracasz do menu głównego.", reply_markup=admin_main_kb())
    await callback.answer()
