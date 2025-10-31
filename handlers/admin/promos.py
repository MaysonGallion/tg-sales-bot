# tg-sales-bot/handlers/admin/promos.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.access_guard import is_admin
from keyboards.inline.admin import (
    admin_main_kb,
    promos_list_kb,
    promo_card_kb,
    promo_create_type_kb,
    promo_create_scope_kb,
    promo_choose_city_kb,
    promo_choose_category_kb,
    promo_confirm_kb,
    cancel_kb,
    promo_edit_type_kb,
    promo_edit_scope_kb,
)
from states.admin_states import AddPromoState, EditPromoState
from database.crud import (
    list_promos,
    get_promo_by_id,
    toggle_promo_active,
    delete_promo,
    create_promo,
    update_promo,
)

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
                return
            except Exception:
                pass
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)

async def _render_list(cb: CallbackQuery, state: FSMContext, page: int | None = None):
    if page is None:
        data = await state.get_data()
        page = int(data.get("promos_page", 1))
    rows, has_next = await list_promos(page=page, page_size=PAGE_SIZE)
    has_prev = page > 1
    await state.update_data(promos_page=page)
    await _safe_edit_text(
        cb.message,
        "🎟️ <b>Promokody</b>",
        reply_markup=promos_list_kb(rows, page, has_prev, has_next),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "admin_promos_open")
async def promos_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.update_data(promos_page=1)
    await _render_list(callback, state, page=1)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_promos_page_"))
async def promos_page(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = int(callback.data.split("_")[-1])
    await _render_list(callback, state, page=page)
    await callback.answer()

# --- Карточка промокода

@router.callback_query(F.data.startswith("admin_promos_view_"))
async def promo_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    promo = await get_promo_by_id(pid)
    if not promo:
        await _safe_edit_text(callback.message, "❌ Kod nie znaleziony.", reply_markup=admin_main_kb())
        return await callback.answer()
    text = (
        f"🎟️ <b>Kod:</b> {promo['code']}\n"
        f"🧮 <b>Typ:</b> {promo['type']}\n"
        f"💰 <b>Wartość:</b> {promo['value']}\n"
        f"🗺 <b>Zakres:</b> {promo['scope']}\n"
        f"🏙 <b>Miasto:</b> {promo.get('city') or '-'}\n"
        f"📂 <b>Kategoria:</b> {promo.get('category') or '-'}\n"
        f"🔖 <b>Status:</b> {'ON' if promo['is_active'] else 'OFF'}"
    )
    await _safe_edit_text(callback.message, text, reply_markup=promo_card_kb(promo), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_promo_toggle_"))
async def promo_toggle(callback: CallbackQuery):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await toggle_promo_active(pid)
    promo = await get_promo_by_id(pid)
    await _safe_edit_text(callback.message, "🔁 Przełączono.", reply_markup=promo_card_kb(promo))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_promo_delete_"))
async def promo_delete(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await delete_promo(pid)
    await _render_list(callback, state)
    await callback.answer("🗑 Usunięto kod.")

# --- Редактирование: КОД

@router.callback_query(F.data.startswith("admin_promo_edit_code_"))
async def promo_edit_code_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await state.update_data(edit_promo_id=pid)
    await state.set_state(EditPromoState.waiting_for_code)
    await callback.message.answer("✏️ Podaj nową treść kodu:", reply_markup=cancel_kb())
    await callback.answer()

@router.message(EditPromoState.waiting_for_code)
async def promo_edit_code_save(message: Message, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    code = (message.text or "").strip()
    if not code:
        return await message.answer("❌ Kod nie może być pusty.", reply_markup=cancel_kb())
    await update_promo(pid, code=code)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await message.answer("✅ Zmieniono.", reply_markup=promo_card_kb(promo))

# --- Редактирование: ТИП

@router.callback_query(F.data.startswith("admin_promo_edit_type_"))
async def promo_edit_type_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await state.update_data(edit_promo_id=pid)
    await state.set_state(EditPromoState.waiting_for_type)
    await callback.message.answer("🧮 Wybierz nowy typ zniżki:", reply_markup=promo_edit_type_kb())
    await callback.answer()

@router.callback_query(EditPromoState.waiting_for_type, F.data.startswith("admin_promo_type_"))
async def promo_edit_type_save(callback: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    ptype = callback.data.split("_")[-1]  # percent|fixed
    await update_promo(pid, type=ptype)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await _safe_edit_text(callback.message, "✅ Zmieniono.", reply_markup=promo_card_kb(promo))
    await callback.answer()

# --- Редактирование: ЗНАЧЕНИЕ

@router.callback_query(F.data.startswith("admin_promo_edit_value_"))
async def promo_edit_value_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await state.update_data(edit_promo_id=pid)
    await state.set_state(EditPromoState.waiting_for_value)
    await callback.message.answer("💰 Podaj nową wartość (np. 10 lub 5.99):", reply_markup=cancel_kb())
    await callback.answer()

@router.message(EditPromoState.waiting_for_value)
async def promo_edit_value_save(message: Message, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    try:
        val = float((message.text or "").replace(",", "."))
    except ValueError:
        return await message.answer("❌ Nieprawidłowa liczba.", reply_markup=cancel_kb())
    await update_promo(pid, value=val)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await message.answer("✅ Zmieniono.", reply_markup=promo_card_kb(promo))

# --- Редактирование: ОБЛАСТЬ (scope) + город/категория

@router.callback_query(F.data.startswith("admin_promo_edit_scope_"))
async def promo_edit_scope_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    pid = int(callback.data.split("_")[-1])
    await state.update_data(edit_promo_id=pid)
    await state.set_state(EditPromoState.waiting_for_scope)
    await callback.message.answer("🗺 Wybierz zakres:", reply_markup=promo_edit_scope_kb())
    await callback.answer()

@router.callback_query(EditPromoState.waiting_for_scope, F.data.startswith("admin_promo_scope_"))
async def promo_edit_scope_save(callback: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    scope = callback.data.split("_")[-1]  # global|city|category

    # Сбрасываем прошлые привязки города/категории
    await update_promo(pid, scope=scope, city=None, category=None)

    if scope == "city":
        await state.set_state(EditPromoState.waiting_for_city)
        await callback.message.answer("🏙 Wybierz miasto:", reply_markup=promo_choose_city_kb())
    elif scope == "category":
        await state.set_state(EditPromoState.waiting_for_category)
        await callback.message.answer("📂 Wybierz kategorię:", reply_markup=promo_choose_category_kb())
    else:
        await state.clear()
        promo = await get_promo_by_id(pid)
        await _safe_edit_text(callback.message, "✅ Zmieniono.", reply_markup=promo_card_kb(promo))
    await callback.answer()

@router.callback_query(EditPromoState.waiting_for_city, F.data.startswith("admin_promo_city_"))
async def promo_edit_city_save(callback: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    city_key = callback.data.split("_")[-1]
    city_map = {"gdansk": "Gdańsk", "gdynia": "Gdynia", "sopot": "Sopot"}
    city = city_map.get(city_key)
    await update_promo(pid, city=city)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await _safe_edit_text(callback.message, "✅ Zmieniono.", reply_markup=promo_card_kb(promo))
    await callback.answer()

@router.callback_query(EditPromoState.waiting_for_category, F.data.startswith("admin_promo_cat_"))
async def promo_edit_category_save_cb(callback: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    cat_key = callback.data.split("_")[-1]  # herbata|slodycze
    cat = "herbata" if cat_key == "herbata" else "slodycze"
    await update_promo(pid, category=cat)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await _safe_edit_text(callback.message, "✅ Zmieniono.", reply_markup=promo_card_kb(promo))
    await callback.answer()

@router.message(EditPromoState.waiting_for_category)
async def promo_edit_category_save_text(message: Message, state: FSMContext):
    d = await state.get_data()
    pid = int(d["edit_promo_id"])
    cat = (message.text or "").strip().lower()
    if cat not in {"herbata", "slodycze"}:
        return await message.answer("❌ Dozwolone: herbata / slodycze.", reply_markup=cancel_kb())
    await update_promo(pid, category=cat)
    await state.clear()
    promo = await get_promo_by_id(pid)
    await message.answer("✅ Zmieniono.", reply_markup=promo_card_kb(promo))

# --- Общие «cancel»/«nop»

@router.callback_query(F.data == "admin_cancel")
async def promo_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _safe_edit_text(callback.message, "❌ Anulowano.", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_nop")
async def admin_nop(callback: CallbackQuery):
    await callback.answer(cache_time=1)

# --- Мастер создания нового промокода

@router.callback_query(F.data == "admin_promos_create")
async def promo_create_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.clear()
    await state.set_state(AddPromoState.waiting_for_code)
    await _safe_edit_text(callback.message, "🎟️ Podaj treść nowego kodu:", reply_markup=cancel_kb())
    await callback.answer()

@router.message(AddPromoState.waiting_for_code)
async def promo_create_code(message: Message, state: FSMContext):
    code = (message.text or "").strip()
    if not code:
        return await message.answer("❌ Kod nie może być pusty.", reply_markup=cancel_kb())
    await state.update_data(code=code)
    await state.set_state(AddPromoState.waiting_for_type)
    await message.answer("🧮 Wybierz typ zniżki:", reply_markup=promo_create_type_kb())

@router.callback_query(AddPromoState.waiting_for_type, F.data.startswith("admin_promo_type_"))
async def promo_create_type(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.split("_")[-1]  # percent|fixed
    await state.update_data(ptype=ptype)
    await state.set_state(AddPromoState.waiting_for_value)
    await _safe_edit_text(callback.message, "💰 Podaj wartość (np. 10 lub 5.99):", reply_markup=cancel_kb())
    await callback.answer()

@router.message(AddPromoState.waiting_for_value)
async def promo_create_value(message: Message, state: FSMContext):
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        return await message.answer("❌ Nieprawidłowa liczba.", reply_markup=cancel_kb())
    await state.update_data(value=value)
    await state.set_state(AddPromoState.waiting_for_scope)
    await message.answer("🗺 Wybierz zakres działania:", reply_markup=promo_create_scope_kb())

@router.callback_query(AddPromoState.waiting_for_scope, F.data.startswith("admin_promo_scope_"))
async def promo_create_scope(callback: CallbackQuery, state: FSMContext):
    scope = callback.data.split("_")[-1]  # global|city|category
    await state.update_data(scope=scope)

    if scope == "city":
        await state.set_state(AddPromoState.waiting_for_city)
        await _safe_edit_text(callback.message, "🏙 Wybierz miasto:", reply_markup=promo_choose_city_kb())
    elif scope == "category":
        await state.set_state(AddPromoState.waiting_for_category)
        await _safe_edit_text(callback.message, "📂 Wybierz kategorię:", reply_markup=promo_choose_category_kb())
    else:
        await state.set_state(AddPromoState.confirmation)
        data = await state.get_data()
        summary = (
            f"🎟️ <b>Nowy kod</b>\n"
            f"• kod: <code>{data['code']}</code>\n"
            f"• typ: {data['ptype']}\n"
            f"• wartość: {data['value']}\n"
            f"• zakres: global\n\n"
            f"Zapisać?"
        )
        await _safe_edit_text(callback.message, summary, reply_markup=promo_confirm_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(AddPromoState.waiting_for_city, F.data.startswith("admin_promo_city_"))
async def promo_create_city(callback: CallbackQuery, state: FSMContext):
    city_key = callback.data.split("_")[-1]
    city_map = {"gdansk": "Gdańsk", "gdynia": "Gdynia", "sopot": "Sopot"}
    city = city_map.get(city_key)
    if not city:
        return await callback.answer("Nieznane miasto", show_alert=True)
    await state.update_data(city=city)
    await state.set_state(AddPromoState.confirmation)
    d = await state.get_data()
    summary = (
        f"🎟️ <b>Nowy kod</b>\n"
        f"• kod: <code>{d['code']}</code>\n"
        f"• typ: {d['ptype']}\n"
        f"• wartość: {d['value']}\n"
        f"• zakres: miasto [{city}]\n\n"
        f"Zapisać?"
    )
    await _safe_edit_text(callback.message, summary, reply_markup=promo_confirm_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(AddPromoState.waiting_for_category, F.data.startswith("admin_promo_cat_"))
async def promo_create_category_cb(callback: CallbackQuery, state: FSMContext):
    cat_key = callback.data.split("_")[-1]  # herbata|slodycze
    cat = "herbata" if cat_key == "herbata" else "slodycze"
    await state.update_data(category=cat)
    await state.set_state(AddPromoState.confirmation)
    d = await state.get_data()
    summary = (
        f"🎟️ <b>Nowy kod</b>\n"
        f"• kod: <code>{d['code']}</code>\n"
        f"• typ: {d['ptype']}\n"
        f"• wartość: {d['value']}\n"
        f"• zakres: kategoria [{cat}]\n\n"
        f"Zapisać?"
    )
    await _safe_edit_text(callback.message, summary, reply_markup=promo_confirm_kb(), parse_mode="HTML")
    await callback.answer()

@router.message(AddPromoState.waiting_for_category)
async def promo_create_category(message: Message, state: FSMContext):
    cat = (message.text or "").strip().lower()
    if cat not in {"herbata", "slodycze"}:
        return await message.answer("❌ Dozwolone: herbata / slodycze.", reply_markup=cancel_kb())
    await state.update_data(category=cat)
    await state.set_state(AddPromoState.confirmation)
    d = await state.get_data()
    summary = (
        f"🎟️ <b>Nowy kod</b>\n"
        f"• kod: <code>{d['code']}</code>\n"
        f"• typ: {d['ptype']}\n"
        f"• wartość: {d['value']}\n"
        f"• zakres: kategoria [{cat}]\n\n"
        f"Zapisać?"
    )
    await message.answer(summary, parse_mode="HTML", reply_markup=promo_confirm_kb())

@router.callback_query(AddPromoState.confirmation, F.data == "admin_promo_save")
async def promo_create_save(callback: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    await create_promo(
        code=d["code"],
        ptype=d["ptype"],
        value=float(d["value"]),
        scope=d["scope"],
        city=d.get("city"),
        category=d.get("category"),
        is_active=True,
        starts_at=None,
        ends_at=None,
        max_uses_total=None,
        max_uses_per_user=1,
    )
    await state.clear()
    await _safe_edit_text(callback.message, "✅ Zapisano nowy kod.", reply_markup=admin_main_kb())
    # сразу список (1-я страница), тем же сообщением
    await promos_open(callback, state)
    await callback.answer()
