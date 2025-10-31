# tg-sales-bot/handlers/admin/consents.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.access_guard import is_admin
from database.crud.admin_consents import list_admin_consents, get_admin_consent
from keyboards.inline.admin import consents_list_kb, consent_card_kb

router = Router()
PAGE_SIZE = 10

# Универсальный helper: сначала пытаемся отредактировать текущее сообщение,
# если "message is not modified" — обновляем только клавиатуру,
# если редактировать нельзя — отправляем новое (крайний случай).
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
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )

@router.callback_query(F.data == "admin_consents_open")
async def consents_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.update_data(consents_page=1)
    await _render_list(callback, state, 1)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_consents_page_"))
async def consents_page(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    page = int(callback.data.split("_")[-1])
    await state.update_data(consents_page=page)
    await _render_list(callback, state, page)
    await callback.answer()

async def _render_list(callback: CallbackQuery, state: FSMContext, page: int):
    rows, has_next = await list_admin_consents(page=page, page_size=PAGE_SIZE)
    has_prev = page > 1

    text = "📑 <b>Zgody administratorów</b>\nWersje i podpisy."
    # ВАЖНО: редактируем текущее сообщение, а не отправляем новое
    await _safe_edit_text(
        callback.message,
        text,
        reply_markup=consents_list_kb(rows, page, has_prev, has_next),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("admin_consents_view_"))
async def consents_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    cid = int(callback.data.split("_")[-1])
    row = await get_admin_consent(cid)
    if not row:
        # тоже редактируем, чтобы не плодить сообщений
        await _safe_edit_text(callback.message, "❌ Pozycja nie znaleziona.")
        return await callback.answer()

    text = (
        f"🧾 <b>ZGODA #{row['id']}</b>\n"
        f"👤 {row.get('accepted_full_name') or '-'} (@{row.get('accepted_username') or '-'})\n"
        f"🆔 {row['admin_telegram_id']}\n"
        f"📌 wersja: <b>{row['version']}</b>\n"
        f"⏱ {row['accepted_at']}\n\n"
        f"--- <b>Treść zaakceptowana</b> ---\n"
        f"{row.get('accepted_text') or '(brak)'}"
    )

    # И тут — редактируем текущее сообщение
    await _safe_edit_text(
        callback.message,
        text,
        reply_markup=consent_card_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
