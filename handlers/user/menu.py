# tg-sales-bot/handlers/user/menu.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.logger import logger
from states.user_states import PromoStates

from database.crud import (
    get_promo_by_code_active,
    can_use_promo,
    set_user_active_promo,
    clear_user_active_promo,
    get_setting,
)

router = Router()

# Мини-клавиатура: только «Главное меню»
def _main_only_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

# Безопасно редактируем сообщение, чтобы не плодить дублей и не ловить «message is not modified»
async def _safe_edit_text(msg: types.Message, text: str, reply_markup=None, parse_mode="HTML", disable_web_page_preview=True):
    try:
        await msg.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "message is not modified" in s:
            # Текст тот же — попробуем обновить только клавиатуру
            try:
                await msg.edit_reply_markup(reply_markup=reply_markup)
            except Exception:
                pass
        else:
            # Сообщение невозможно отредактировать (удалено/старое) — пришлём новое
            await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)

# --------- Пользовательское меню: 3 пункта — промокод / регламент / помощь ---------

REGULAMIN_HEADER = "📜 <b>Regulamin sklepu</b>\n"
REGULAMIN_MANDATORY_FOOTER = (
    "\n\n──────────\n"
    "<i>Uwaga: Twórcy oprogramowania (bot) nie ponoszą odpowiedzialności za treści i ustalenia sprzedawcy. "
    "Korzystanie z bota oznacza akceptację zasad przedstawionych powyżej przez administratora sklepu.</i>"
)
SUPPORT_HEADER = "💬 <b>Pomoc / Wsparcie</b>\n"

@router.callback_query(F.data == "menu_bonus")
async def menu_bonus(callback: CallbackQuery, state: FSMContext):
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: menu_bonus")
    await state.set_state(PromoStates.waiting_for_code)
    txt = (
        "🎟️ Wpisz <b>kod promocyjny</b> w kolejnej wiadomości.\n"
        "Aby usunąć aktywny kod, wyślij: <code>USUN</code>"
    )
    await _safe_edit_text(callback.message, txt, parse_mode="HTML", reply_markup=_main_only_kb())
    await callback.answer()

@router.callback_query(F.data == "menu_regulamin")
async def menu_regulamin(callback: CallbackQuery, state: FSMContext):
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: menu_regulamin")
    content = await get_setting("regulamin") or ""
    full = f"{REGULAMIN_HEADER}{content}{REGULAMIN_MANDATORY_FOOTER}"
    await _safe_edit_text(callback.message, full, parse_mode="HTML", reply_markup=_main_only_kb(), disable_web_page_preview=True)
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "menu_pomoc")
async def menu_pomoc(callback: CallbackQuery, state: FSMContext):
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: menu_pomoc")
    content = await get_setting("support") or ""
    full = f"{SUPPORT_HEADER}{content}"
    await _safe_edit_text(callback.message, full, parse_mode="HTML", reply_markup=_main_only_kb(), disable_web_page_preview=True)
    await state.clear()
    await callback.answer()

# --------- Ввод кода (сохранено из твоей логики) ---------

@router.message(PromoStates.waiting_for_code)
async def apply_promo_code(message: types.Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw:
        return await message.answer("❌ Podaj kod lub wpisz: <code>USUN</code>", parse_mode="HTML")

    if raw.upper() == "USUN":
        await clear_user_active_promo(message.from_user.id)
        await state.clear()
        return await message.answer("✅ Aktywny kod został usunięty.", reply_markup=_main_only_kb())

    promo = await get_promo_by_code_active(raw)
    if not promo:
        return await message.answer("❌ Kod nieprawidłowy lub nieaktywny.", reply_markup=_main_only_kb())

    ok_user = await can_use_promo(message.from_user.id, promo)
    if not ok_user:
        await state.clear()
        return await message.answer("❌ Osiągnięto limit użyć tego kodu dla Twojego konta.", reply_markup=_main_only_kb())

    await set_user_active_promo(message.from_user.id, promo["id"])
    await state.clear()
    await message.answer(
        f"✅ Kod <b>{promo['code']}</b> zapisany. Zostanie automatycznie zastosowany przy zakupie, jeśli będzie pasował do oferty.",
        parse_mode="HTML",
        reply_markup=_main_only_kb()
    )
