# tg-sales-bot/handlers/user/history.py
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database.crud import get_user_orders
from keyboards.inline.menu import main_menu_inline_kb
from utils.logger import logger

router = Router()

# --- локальный helper: безопасное редактирование текста (без спама в чат) ---
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
            # Контент тот же — попробуем только клавиатуру
            try:
                await msg.edit_reply_markup(reply_markup=reply_markup)
            except Exception:
                pass
        else:
            # Не можем редактировать (устарело/удалено) — отправим новое
            await msg.answer(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )

def _history_kb() -> InlineKeyboardMarkup:
    # единственная кнопка — «Главное меню», но в рамках истории
    # используем отдельный callback, чтобы СМЕНЯТЬ текущее сообщение, а не удалять
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="history_to_main")]
    ])

@router.callback_query(F.data == "menu_historia")
async def show_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    logger.info(f"🧭 Historia: request by {user_id}")

    orders = await get_user_orders(user_id, limit=10)

    if not orders:
        text = "📖 Brak zamówień w historii."
        await _safe_edit_text(callback.message, text, reply_markup=_history_kb())
        return await callback.answer()

    lines = ["📖 <b>Twoje ostatnie zamówienia:</b>"]
    for o in orders:
        created = o["created_at"].strftime('%Y-%m-%d %H:%M')
        method = "BLIK" if o["payment_method"] == "blik" else "gotówka"
        lines.append(
            f"#{o['id']} | {created} | {o['city']} • {o['category']} • "
            f"{o['price']} zł • {method} • status: <b>{o['status']}</b>"
        )

    await _safe_edit_text(callback.message, "\n".join(lines), reply_markup=_history_kb())
    await callback.answer()

@router.callback_query(F.data == "history_to_main")
async def history_to_main(callback: CallbackQuery):
    # Возвращаем то же сообщение к главному меню (через edit_text)
    await _safe_edit_text(
        callback.message,
        "🏠 Wróciłeś do menu głównego. Wybierz opcję:",
        reply_markup=main_menu_inline_kb()
    )
    await callback.answer()
