# tg-sales-bot/handlers/admin/orders.py
from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.access_guard import is_admin
from database.crud import get_orders_page, get_order_by_id, set_order_status

from keyboards.inline.admin import (
    orders_filters_kb,
    orders_list_kb,
    orders_empty_list_kb,
    order_card_kb,
    admin_main_kb,
)

router = Router()

DEFAULT_STATUS = "new"
PAGE_SIZE = 10

def _status_title(status: str) -> str:
    mapping = {
        "new": "nowe",
        "in_progress": "w trakcie",
        "done": "zrealizowane",
        "cancelled": "anulowane",
        "all": "wszystkie",
    }
    return mapping.get(status, status)

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

async def _render_list_in_one(callback: CallbackQuery, state: FSMContext):
    """Единое сообщение: заголовок с фильтром + список/пусто + навигация."""
    data = await state.get_data()
    status = data.get("orders_status", DEFAULT_STATUS)
    page = int(data.get("orders_page", 1))

    rows, has_next = await get_orders_page(
        status=None if status == "all" else status,
        city=None,
        page=page,
        page_size=PAGE_SIZE
    )
    has_prev = page > 1

    header = f"🧾 <b>Zamówienia</b> — filtr: <code>{_status_title(status)}</code>"
    if rows:
        kb = orders_list_kb(rows, page, has_prev, has_next, status)
        text = header + "\n\n📜 Lista zamówień:"
    else:
        kb = orders_empty_list_kb()
        text = header + "\n\n❌ Brak zamówień dla tego filtra."

    await _safe_edit_text(callback.message, text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_orders_open")
async def orders_open(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    await state.update_data(
        orders_status=DEFAULT_STATUS,
        orders_page=1,
        current_order_id=None,
    )
    await _render_list_in_one(callback, state)
    await callback.answer()

@router.callback_query(F.data == "admin_orders_filters")
async def orders_filters(callback: CallbackQuery, state: FSMContext):
    # В этом упрощённом UX просто обновляем клавиатуру фильтров «на месте»
    data = await state.get_data()
    status = data.get("orders_status", DEFAULT_STATUS)
    text = f"🧾 <b>Zamówienia</b> — filtr: <code>{_status_title(status)}</code>\n\n📜 Lista zamówień:"
    await _safe_edit_text(callback.message, text, reply_markup=orders_filters_kb(status), parse_mode="HTML")
    await callback.answer("Wybierz filtr.")

@router.callback_query(F.data.startswith("admin_orders_filter_"))
async def orders_filter_set(callback: CallbackQuery, state: FSMContext):
    status = callback.data.replace("admin_orders_filter_", "", 1)  # new|in_progress|done|cancelled|all
    await state.update_data(orders_status=status, orders_page=1)
    await _render_list_in_one(callback, state)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_orders_page_"))
async def orders_page_set(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.replace("admin_orders_page_", "", 1))
    await state.update_data(orders_page=page)
    await _render_list_in_one(callback, state)
    await callback.answer()

@router.callback_query(F.data == "admin_orders_nop")
async def orders_nop(callback: CallbackQuery):
    await callback.answer("")

@router.callback_query(F.data.startswith("admin_orders_view_"))
async def orders_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return
    order_id = int(callback.data.replace("admin_orders_view_", "", 1))
    await state.update_data(current_order_id=order_id)
    order = await get_order_by_id(order_id)
    if not order:
        await _safe_edit_text(callback.message, "❌ Zamówienie nie znalezione.", reply_markup=admin_main_kb())
        return await callback.answer()

    text = (
        f"🧾 <b>Zamówienie #{order['id']}</b>\n"
        f"👤 {order['telegram_id']}\n"
        f"📦 product_id: {order['product_id']}\n"
        f"🏙 {order['city']} • 📂 {order['category']}\n"
        f"💰 {order['price']} zł\n"
        f"💳 {order['payment_method'].upper()}\n"
        f"📍 {order['address'] or '-'}\n"
        f"🧾 msg_id: {order['payment_proof_message_id'] or '-'}\n"
        f"⏱ {order['created_at']}\n"
        f"🔖 status: <b>{order['status']}</b>"
    )
    await _safe_edit_text(callback.message, text, reply_markup=order_card_kb(order['status']), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_orders_set_"))
async def orders_set_status(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        return

    status = callback.data.replace("admin_orders_set_", "", 1)  # in_progress|done|cancelled
    allowed = {"in_progress", "done", "cancelled"}
    if status not in allowed:
        return await callback.answer("Nieznany status.", show_alert=True)

    data = await state.get_data()
    order_id = int(data.get("current_order_id", 0))
    if not order_id:
        return await callback.answer("Otwórz najpierw kartę zamówienia.", show_alert=True)

    await set_order_status(order_id, status)
    order = await get_order_by_id(order_id)

    text = (
        f"✅ Zmieniono status na: <b>{_status_title(status)}</b>\n\n"
        f"🧾 <b>Zamówienie #{order['id']}</b>\n"
        f"👤 {order['telegram_id']}\n"
        f"📦 product_id: {order['product_id']}\n"
        f"🏙 {order['city']} • 📂 {order['category']}\n"
        f"💰 {order['price']} zł\n"
        f"💳 {order['payment_method'].upper()}\n"
        f"📍 {order['address'] or '-'}\n"
        f"🧾 msg_id: {order['payment_proof_message_id'] or '-'}\n"
        f"⏱ {order['created_at']}\n"
        f"🔖 status: <b>{order['status']}</b>"
    )
    await _safe_edit_text(callback.message, text, reply_markup=order_card_kb(order['status']), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_orders_back_to_list")
async def orders_back_to_list(callback: CallbackQuery, state: FSMContext):
    await _render_list_in_one(callback, state)
    await callback.answer()
