# tg-sales-bot/handlers/admin/pages.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.access_guard import is_admin
from database.crud import get_setting, set_setting
from states.admin_states import EditPagesState
from keyboards.inline.admin import pages_edit_menu_kb, pages_back_kb

router = Router()

REGULAMIN_HEADER = "📜 <b>Regulamin sklepu</b>\n"
REGULAMIN_MANDATORY_FOOTER = (
    "\n\n──────────\n"
    "<i>Uwaga: Twórcy oprogramowania (bot) nie ponoszą odpowiedzialności za treści i ustalenia sprzedawcy. "
    "Korzystanie z bota oznacza akceptację zasad przedstawionych powyżej przez administratora sklepu.</i>"
)
SUPPORT_HEADER = "💬 <b>Pomoc / Wsparcie</b>\n"

KEY_REGULAMIN = "regulamin"
KEY_SUPPORT = "support"

async def _render_page_preview(callback: CallbackQuery, key: str, text: str | None):
    content = (text or "").strip()
    if key == KEY_REGULAMIN:
        full = f"{REGULAMIN_HEADER}{content}{REGULAMIN_MANDATORY_FOOTER}"
    else:
        full = f"{SUPPORT_HEADER}{content}"

    try:
        await callback.message.edit_text(full, parse_mode="HTML", reply_markup=pages_edit_menu_kb(), disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(full, parse_mode="HTML", reply_markup=pages_edit_menu_kb(), disable_web_page_preview=True)

@router.callback_query(F.data == "admin_pages_regulamin")
async def open_regulamin(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.update_data(pages_current=KEY_REGULAMIN)
    text = await get_setting(KEY_REGULAMIN)
    await _render_page_preview(callback, KEY_REGULAMIN, text)
    await callback.answer()

@router.callback_query(F.data == "admin_pages_support")
async def open_support(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.update_data(pages_current=KEY_SUPPORT)
    text = await get_setting(KEY_SUPPORT)
    await _render_page_preview(callback, KEY_SUPPORT, text)
    await callback.answer()

@router.callback_query(F.data == "admin_pages_edit")
async def pages_edit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    d = await state.get_data()
    cur = d.get("pages_current")
    if cur == KEY_REGULAMIN:
        await state.set_state(EditPagesState.waiting_for_regulamin)
        await callback.message.edit_text(
            "✏️ <b>Edytuj treść Regulaminu</b>\nWyślij nową treść jedną wiadomością (HTML dozwolony).",
            parse_mode="HTML", reply_markup=pages_back_kb()
        )
    elif cur == KEY_SUPPORT:
        await state.set_state(EditPagesState.waiting_for_support)
        await callback.message.edit_text(
            "✏️ <b>Edytuj treść Pomocy</b>\nWyślij nową treść jedną wiadomością (HTML dozwolony).",
            parse_mode="HTML", reply_markup=pages_back_kb()
        )
    await callback.answer()

@router.message(EditPagesState.waiting_for_regulamin)
async def save_regulamin(message: Message, state: FSMContext):
    content = (message.html_text or message.text or "").strip()
    await set_setting(KEY_REGULAMIN, content)
    await state.clear()
    await message.answer("✅ Zapisano.")
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_page_preview(fake_cb, KEY_REGULAMIN, content)

@router.message(EditPagesState.waiting_for_support)
async def save_support(message: Message, state: FSMContext):
    content = (message.html_text or message.text or "").strip()
    await set_setting(KEY_SUPPORT, content)
    await state.clear()
    await message.answer("✅ Zapisano.")
    fake_cb = type("obj",(object,),{"message":message})()
    await _render_page_preview(fake_cb, KEY_SUPPORT, content)
