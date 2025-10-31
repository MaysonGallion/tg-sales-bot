# tg-sales-bot/handlers/admin/dicts.py
# Админ-редактор справочников: города и категории

from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from utils.access_guard import is_admin
from states.admin_states import DictsState

from keyboards.inline.admin import (
    dicts_main_kb,
    cities_list_kb,
    city_card_kb,
    categories_list_kb,
    category_card_kb,
    admin_main_kb,
)

from database.crud import (
    # города
    list_cities, get_city_by_id, add_city, rename_city,
    toggle_city_active, delete_city_by_id,
    # категории (глобальные)
    list_categories, get_category_by_id,
    add_category, rename_category_name, recode_category_code,
    toggle_category_active, delete_category_by_id,
    # привязка город↔категория
    list_categories_with_flag, assign_category_to_city, unassign_category_from_city,
)

router = Router()


# ───────── helper: безопасный edit_text ─────────
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
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup,
                         disable_web_page_preview=disable_web_page_preview)


# ───────── корневое меню ─────────
@router.callback_query(F.data == "admin_dicts_open")
async def dicts_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.set_state(DictsState.entry)
    await _safe_edit_text(callback.message, "🗂️ Słowniki: miasta i kategorie", reply_markup=dicts_main_kb())
    await callback.answer()


# ───────── города: список/страницы ─────────
@router.callback_query(F.data == "admin_cities_open")
async def cities_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.set_state(DictsState.cities_list)
    page = 1
    rows, has_next = await list_cities(page=page, page_size=10)
    await _safe_edit_text(callback.message, "🏙️ <b>Miasta</b>",
                          reply_markup=cities_list_kb(rows, page, has_prev=False, has_next=has_next),
                          parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cities_page_"))
async def cities_page(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = int(callback.data.split("_")[-1])
    rows, has_next = await list_cities(page=page, page_size=10)
    await _safe_edit_text(callback.message, "🏙️ <b>Miasta</b>",
                          reply_markup=cities_list_kb(rows, page, has_prev=page > 1, has_next=has_next),
                          parse_mode="HTML")
    await callback.answer()


# ───────── города: карточка / toggle ─────────
@router.callback_query(F.data.startswith("admin_city_view_"))
async def city_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    city_id = int(callback.data.split("_")[-1])
    row = await get_city_by_id(city_id)
    if not row:
        await _safe_edit_text(callback.message, "❌ Miasto nie znalezione.", reply_markup=admin_main_kb())
        return await callback.answer()
    text = (
        f"🏙️ <b>Miasto</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Nazwa: <b>{row['name']}</b>\n"
        f"Status: {'🟢 aktywne' if row['is_active'] else '🔴 wyłączone'}"
    )
    await _safe_edit_text(callback.message, text, reply_markup=city_card_kb(row), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_city_toggle_"))
async def city_toggle(callback: CallbackQuery):
    if not is_admin(callback):
        return
    city_id = int(callback.data.split("_")[-1])
    await toggle_city_active(city_id)
    row = await get_city_by_id(city_id)
    if not row:
        return await _safe_edit_text(callback.message, "❌ Miasto nie znalezione.", reply_markup=admin_main_kb())
    text = (
        f"✅ Zmieniono status.\n\n"
        f"🏙️ <b>Miasto</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Nazwa: <b>{row['name']}</b>\n"
        f"Status: {'🟢 aktywne' if row['is_active'] else '🔴 wyłączone'}"
    )
    await _safe_edit_text(callback.message, text, reply_markup=city_card_kb(row), parse_mode="HTML")
    await callback.answer()


# ───────── города: удаление с подтверждением ─────────
def _city_delete_confirm_kb(city_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Potwierdź usunięcie", callback_data=f"admin_city_delete_do_{city_id}")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data=f"admin_city_view_{city_id}")],
    ])


def _after_delete_city_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć do listy", callback_data="admin_cities_open")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ])


@router.callback_query(F.data.regexp(r"^admin_city_delete_(\d+)$"))
async def city_delete_ask(callback: CallbackQuery):
    if not is_admin(callback):
        return
    city_id = int(callback.data.rsplit("_", 1)[-1])
    row = await get_city_by_id(city_id)
    if not row:
        await _safe_edit_text(callback.message, "❌ Miasto nie znalezione.", reply_markup=admin_main_kb())
        return await callback.answer()
    txt = (
        f"❗ Czy na pewno usunąć miasto <b>{row['name']}</b>?\n\n"
        f"Usuniemy również wszystkie <b>produkty</b> z tym miastem oraz <b>powiązania kategorii</b>."
    )
    await _safe_edit_text(callback.message, txt, reply_markup=_city_delete_confirm_kb(city_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_city_delete_do_"))
async def city_delete_do(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    city_id = int(callback.data.replace("admin_city_delete_do_", "", 1))
    ok = await delete_city_by_id(city_id)
    if ok:
        text = "✅ Miasto zostało usunięte.\n\nCo dalej?"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Wróć do listy miast", callback_data="admin_cities_open")],
            [InlineKeyboardButton(text="🏠 Menu admina", callback_data="admin_menu_admin")],
        ])
        await _safe_edit_text(callback.message, text, reply_markup=kb, parse_mode="HTML")
    else:
        await _safe_edit_text(
            callback.message,
            "❌ Nie udało się usunąć miasta (może już nie istnieje).",
            reply_markup=_after_delete_city_kb(),
            parse_mode="HTML"
        )
    await callback.answer()


# ───────── города: добавление/переименование ─────────
def _city_add_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_cities_open")],
    ])


@router.callback_query(F.data == "admin_city_add")
async def city_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.set_state(DictsState.waiting_for_city_name)
    await _safe_edit_text(callback.message, "✏️ Podaj nazwę nowego miasta:", reply_markup=_city_add_kb())
    await callback.answer()


@router.message(DictsState.waiting_for_city_name)
async def city_add_save(message: types.Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        return await message.answer("❌ Nazwa nie może być pusta.", reply_markup=_city_add_kb())
    ok = await add_city(name)  # создаётся выключенным и без категорий
    await state.clear()
    page = 1
    rows, has_next = await list_cities(page=page, page_size=10)
    prefix = "✅ Dodano miasto.\n\n" if ok else "⚠️ Nie udało się dodać (duplikat?).\n\n"
    await message.answer(prefix + "🏙️ <b>Miasta</b>", parse_mode="HTML",
                         reply_markup=cities_list_kb(rows, page, has_prev=False, has_next=has_next))


def _city_rename_back_kb(city_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data=f"admin_city_view_{city_id}")],
    ])


@router.callback_query(F.data.startswith("admin_city_rename_"))
async def city_rename_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    city_id = int(callback.data.split("_")[-1])
    await state.update_data(city_id=city_id)
    await state.set_state(DictsState.waiting_for_city_rename)
    await _safe_edit_text(callback.message, "✏️ Podaj nową nazwę miasta:", reply_markup=_city_rename_back_kb(city_id))
    await callback.answer()


@router.message(DictsState.waiting_for_city_rename)
async def city_rename_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    city_id = int(data.get("city_id"))
    new_name = (message.text or "").strip()
    if not new_name:
        return await message.answer("❌ Nazwa nie może być pusta.", reply_markup=_city_rename_back_kb(city_id))
    ok = await rename_city(city_id, new_name)
    await state.clear()
    row = await get_city_by_id(city_id)
    if not row:
        return await message.answer("❌ Miasto nie znalezione.", reply_markup=admin_main_kb())
    prefix = "✅ Zmieniono nazwę.\n\n" if ok else "⚠️ Nie udało się zmienić.\n\n"
    text = (
            prefix +
            f"🏙️ <b>Miasto</b>\n"
            f"ID: <code>{row['id']}</code>\n"
            f"Nazwa: <b>{row['name']}</b>\n"
            f"Status: {'🟢 aktywne' if row['is_active'] else '🔴 wyłączone'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=city_card_kb(row))


# ───────── КАТЕГОРИИ ГОРОДА: просмотр и назначение ─────────

def _city_cats_kb(city_id: int, rows: list[dict]) -> InlineKeyboardMarkup:
    """
    rows: [{id, code, name, assigned: bool}]
    """
    kb_rows = []
    for r in rows:
        mark = "✅" if r.get("assigned") else "➕"
        kb_rows.append([InlineKeyboardButton(
            text=f"{mark} {r['name']} ({r['code']})",
            callback_data=f"admin_city_cat_toggle_{city_id}_{r['id']}"
        )])
    kb_rows.append([InlineKeyboardButton(text="🔙 Wróć do miasta", callback_data=f"admin_city_view_{city_id}")])
    kb_rows.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


@router.callback_query(F.data.startswith("admin_city_cats_open_"))
async def city_cats_open(callback: CallbackQuery):
    if not is_admin(callback):
        return
    city_id = int(callback.data.split("_")[-1])
    city = await get_city_by_id(city_id)
    if not city:
        await _safe_edit_text(callback.message, "❌ Miasto nie znalezione.", reply_markup=admin_main_kb())
        return await callback.answer()
    rows = await list_categories_with_flag(city_id)  # [{id, code, name, assigned}]
    text = (
        f"🏙️ <b>{city['name']}</b> — kategorie dostępne w tym mieście:\n"
        f"<i>Tapnij, żeby dodać/usunąć.</i>"
    )
    await _safe_edit_text(callback.message, text, reply_markup=_city_cats_kb(city_id, rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_city_cat_toggle_(\d+)_(\d+)$"))
async def city_cat_toggle(callback: CallbackQuery):
    if not is_admin(callback):
        return
    _, city_id_str, cat_id_str = callback.data.rsplit("_", 2)
    city_id = int(city_id_str)
    cat_id = int(cat_id_str)

    rows = await list_categories_with_flag(city_id)
    cur = next((r for r in rows if r["id"] == cat_id), None)
    if not cur:
        await _safe_edit_text(callback.message, "❌ Kategoria nie znaleziona.",
                              reply_markup=_city_cats_kb(city_id, rows))
        return await callback.answer()

    if cur.get("assigned"):
        await unassign_category_from_city(city_id, cat_id)
    else:
        await assign_category_to_city(city_id, cat_id)

    # перерисовать экран
    rows = await list_categories_with_flag(city_id)
    city = await get_city_by_id(city_id)
    text = (
        f"🏙️ <b>{city['name']}</b> — kategorie dostępne w tym mieście:\n"
        f"<i>Tapnij, żeby dodać/usunąć.</i>"
    )
    await _safe_edit_text(callback.message, text,
                          reply_markup=_city_cats_kb(city_id, rows), parse_mode="HTML")
    await callback.answer()


# ───────── категории: список/страницы ─────────
@router.callback_query(F.data == "admin_categories_open")
async def categories_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = 1
    rows, has_next = await list_categories(page=page, page_size=10)
    await _safe_edit_text(callback.message, "📂 <b>Kategorie</b>",
                          reply_markup=categories_list_kb(rows, page, has_prev=False, has_next=has_next),
                          parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_categories_page_"))
async def categories_page(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = int(callback.data.split("_")[-1])
    rows, has_next = await list_categories(page=page, page_size=10)
    await _safe_edit_text(callback.message, "📂 <b>Kategorie</b>",
                          reply_markup=categories_list_kb(rows, page, has_prev=page > 1, has_next=has_next),
                          parse_mode="HTML")
    await callback.answer()


# ───────── категория: карточка / toggle ─────────
@router.callback_query(F.data.startswith("admin_category_view_"))
async def category_view(callback: CallbackQuery):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.split("_")[-1])
    row = await get_category_by_id(cat_id)
    if not row:
        await _safe_edit_text(callback.message, "❌ Kategoria nie znaleziona.", reply_markup=admin_main_kb())
        return await callback.answer()
    text = (
        f"📂 <b>Kategoria</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Code: <code>{row['code']}</code>\n"
        f"Nazwa: <b>{row['name']}</b>\n"
        f"Status: {'🟢 aktywna' if row['is_active'] else '🔴 wyłączona'}"
    )
    await _safe_edit_text(callback.message, text, reply_markup=category_card_kb(row), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_toggle_"))
async def category_toggle(callback: CallbackQuery):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.split("_")[-1])
    await toggle_category_active(cat_id)
    row = await get_category_by_id(cat_id)
    if not row:
        return await _safe_edit_text(callback.message, "❌ Kategoria nie znaleziona.", reply_markup=admin_main_kb())
    text = (
        f"✅ Zmieniono status.\n\n"
        f"📂 <b>Kategoria</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Code: <code>{row['code']}</code>\n"
        f"Nazwa: <b>{row['name']}</b>\n"
        f"Status: {'🟢 aktywna' if row['is_active'] else '🔴 wyłączona'}"
    )
    await _safe_edit_text(callback.message, text, reply_markup=category_card_kb(row), parse_mode="HTML")
    await callback.answer()


# ───────── категория: добавление ─────────
def _category_add_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_categories_open")],
    ])


@router.callback_query(F.data == "admin_category_add")
async def category_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.set_state(DictsState.waiting_for_category_name)
    text = (
        "✏️ Podaj <b>nową kategorię</b> w formacie:\n"
        "<code>code;Nazwa</code>\n\n"
        "Np.: <code>herbata;Herbaty</code>"
    )
    await _safe_edit_text(callback.message, text, parse_mode="HTML", reply_markup=_category_add_kb())
    await callback.answer()


@router.message(DictsState.waiting_for_category_name)
async def category_add_save(message: types.Message, state: FSMContext):
    raw = (message.text or "").strip()
    try:
        code, title = [s.strip() for s in raw.split(";", 1)]
    except Exception:
        return await message.answer("❌ Format: <code>code;Nazwa</code>", parse_mode="HTML",
                                    reply_markup=_category_add_kb())

    ok = await add_category(code, title)
    await state.clear()
    page = 1
    rows, has_next = await list_categories(page=page, page_size=10)
    prefix = "✅ Dodano kategorię.\n\n" if ok else "⚠️ Nie udało się dodać (duplikat?).\n\n"
    await message.answer(prefix + "📂 <b>Kategorie</b>", parse_mode="HTML",
                         reply_markup=categories_list_kb(rows, page, has_prev=False, has_next=has_next))


# ───────── категория: ввод названия ИЛИ нового кода ─────────
def _cat_back_kb(cat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data=f"admin_category_view_{cat_id}")],
    ])


@router.callback_query(F.data.startswith("admin_category_rename_"))
async def category_rename_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.split("_")[-1])
    await state.update_data(cat_id=cat_id, mode="rename")
    await state.set_state(DictsState.waiting_for_category_rename)
    await _safe_edit_text(callback.message, "✏️ Podaj nowe <b>nazwa</b> kategorii:", parse_mode="HTML",
                          reply_markup=_cat_back_kb(cat_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_recode_"))
async def category_recode_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.split("_")[-1])
    await state.update_data(cat_id=cat_id, mode="recode")
    await state.set_state(DictsState.waiting_for_category_rename)
    await _safe_edit_text(callback.message, "✏️ Podaj <b>nowy kod</b> kategorii:", parse_mode="HTML",
                          reply_markup=_cat_back_kb(cat_id))
    await callback.answer()


@router.message(DictsState.waiting_for_category_rename)
async def category_rename_or_recode_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat_id = int(data.get("cat_id"))
    mode = data.get("mode")  # "rename" | "recode"
    text = (message.text or "").strip()
    await state.clear()

    if mode == "recode":
        ok, msg = await recode_category_code(cat_id, text)
        row = await get_category_by_id(cat_id)
        if not row:
            return await message.answer("❌ Kategoria nie znaleziona.", reply_markup=admin_main_kb())
        prefix = "✅ " if ok else "❌ "
        await message.answer(prefix + msg, parse_mode="HTML", reply_markup=category_card_kb(row))
        return

    if not text:
        return await message.answer("❌ Nazwa nie może być pusta.", reply_markup=_cat_back_kb(cat_id))
    ok = await rename_category_name(cat_id, text)
    row = await get_category_by_id(cat_id)
    if not row:
        return await message.answer("❌ Kategoria nie znaleziona.", reply_markup=admin_main_kb())
    prefix = "✅ Zmieniono nazwę.\n\n" if ok else "⚠️ Nie udało się zmienić.\n\n"
    info = (
        f"📂 <b>Kategoria</b>\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Code: <code>{row['code']}</code>\n"
        f"Nazwa: <b>{row['name']}</b>\n"
        f"Status: {'🟢 aktywna' if row['is_active'] else '🔴 wyłączona'}"
    )
    await message.answer(prefix + info, parse_mode="HTML", reply_markup=category_card_kb(row))


# ───────── категория: удаление ─────────
def _category_after_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć do listy", callback_data="admin_categories_open")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ])


def _category_delete_confirm_kb(cat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Potwierdź usunięcie", callback_data=f"admin_category_delete_confirm_{cat_id}")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data=f"admin_category_view_{cat_id}")],
    ])


@router.callback_query(F.data.regexp(r"^admin_category_delete_(\d+)$"))
async def category_delete_ask(callback: CallbackQuery):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.rsplit("_", 1)[-1])
    row = await get_category_by_id(cat_id)
    if not row:
        await _safe_edit_text(callback.message, "❌ Kategoria nie znaleziona.", reply_markup=admin_main_kb())
        return await callback.answer()
    txt = (
        f"❗ Czy na pewno usunąć kategorię <b>{row['name']}</b> (<code>{row['code']}</code>)?\n\n"
        f"Uwaga: produkty z tą kategorią zostaną ustawione na <b>brak kategorii</b>."
    )
    await _safe_edit_text(callback.message, txt, reply_markup=_category_delete_confirm_kb(cat_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_category_delete_confirm_(\d+)$"))
async def category_delete_do(callback: CallbackQuery):
    if not is_admin(callback):
        return
    cat_id = int(callback.data.rsplit("_", 1)[-1])
    ok = await delete_category_by_id(cat_id)
    await _safe_edit_text(callback.message,
                          ("🗑 Kategorię usunięto." if ok else "❌ Nie udało się usunąć."),
                          reply_markup=_category_after_delete_kb(), parse_mode="HTML")
    await callback.answer("Usunięto." if ok else "Brak zmian.")
