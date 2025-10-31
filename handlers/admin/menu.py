# tg-sales-bot/handlers/admin/menu.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from keyboards.inline.admin import admin_main_kb, admin_legal_accept_kb
from keyboards.inline.menu import main_menu_inline_kb
from utils.access_guard import is_admin
from database.crud import has_consented, set_consented
from messages.pl import LEGAL_CONSENT_VERSION, LEGAL_CONSENT_PROMPT, LEGAL_CONSENT_FULL

router = Router()

CONSENT_VERSION = LEGAL_CONSENT_VERSION

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

# ——— Вход в админку (через главное меню) ———
@router.callback_query(F.data == "show_admin_menu")
async def show_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return

    admin_id = callback.from_user.id
    if not await has_consented(admin_id, CONSENT_VERSION):
        # показываем согласие (редактируем текущее сообщение)
        await _safe_edit_text(
            callback.message,
            LEGAL_CONSENT_PROMPT,
            reply_markup=admin_legal_accept_kb(),
            parse_mode="HTML",
        )
        return await callback.answer()

    await _safe_edit_text(callback.message, "🛠️ Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

# ——— Принятие/отклонение соглашения ———
@router.callback_query(F.data == "admin_legal_accept")
async def admin_legal_accept(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await set_consented(callback.from_user.id, CONSENT_VERSION)
    await _safe_edit_text(callback.message, "✅ Dziękujemy. Zgoda zapisana.\n\n🛠️ Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_legal_decline")
async def admin_legal_decline(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    # Поясняем полную версию и остаёмся в том же сообщении
    await _safe_edit_text(callback.message, LEGAL_CONSENT_FULL, parse_mode="HTML")
    await callback.answer("Dostęp wstrzymany — brak akceptacji.", show_alert=True)

# ——— ГЛАВНЫЕ КНОПКИ НАВИГАЦИИ (единые для всего админ-модуля) ———
@router.callback_query(F.data == "admin_menu_admin")
async def goto_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.clear()
    await _safe_edit_text(callback.message, "🏠 Panel admina:", reply_markup=admin_main_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_menu_user")
async def goto_user_menu(callback: CallbackQuery, state: FSMContext):
    # Возврат в пользовательское главное меню из админки
    await state.clear()
    await _safe_edit_text(callback.message, "🏠 Wróciłeś do menu głównego. Wybierz opcję:", reply_markup=main_menu_inline_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_nop")
async def admin_nop(callback: CallbackQuery):
    await callback.answer(cache_time=1)
