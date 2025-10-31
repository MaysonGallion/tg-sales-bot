# tg-sales-bot/handlers/user/payment.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.user_states import PaymentStates
from database.crud import get_product_by_id
from database.crud import get_user_active_promo, promo_applicable_for, apply_discount
from database.crud import create_order  # ← ДОБАВЛЕНО: сохраняем заказ в БД
from config import BLIK_NUMBER
from keyboards.inline.menu import main_menu_inline_kb

from messages.pl import (
    USER_MENU_CHOOSE_PAYMENT,
    PAYMENT_BLIK_STEP1_TITLE,
    PAYMENT_BLIK_NUMBER_PREFIX,
    PAYMENT_BLIK_INSTR,
    PAYMENT_BLIK_BUTTON_PAID,
    PAYMENT_BLIK_STEP2_PROMPT,
    PAYMENT_BLIK_ERR_NEED_PHOTO_OR_DOC,
    PAYMENT_BLIK_ERR_NEED_CAPTION,
    PAYMENT_BLIK_OK,
    PAYMENT_CASH_PROMPT,
    PAYMENT_CASH_OK,
    ADMIN_ORDER_NEW_HEADER,
    ADMIN_ORDER_DETAILS,
)

from utils.notify import notify_admins, forward_to_admins
from utils.logger import logger

router = Router()

# 💳 Wybór metody płatności
@router.callback_query(F.data == "choose_payment")
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Gotówka na miejscu", callback_data="pay_cash")],
        [InlineKeyboardButton(text="📲 BLIK na numer", callback_data="pay_blik")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    await callback.message.delete()
    await callback.message.answer(
        USER_MENU_CHOOSE_PAYMENT,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# 📲 BLIK — krok 1 (instrukcja)
@router.callback_query(F.data == "pay_blik")
async def handle_blik_payment(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=PAYMENT_BLIK_BUTTON_PAID, callback_data="blik_paid")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    text = (
        f"{PAYMENT_BLIK_STEP1_TITLE}\n\n"
        f"<b>{PAYMENT_BLIK_NUMBER_PREFIX}{BLIK_NUMBER}</b>\n\n"
        f"{PAYMENT_BLIK_INSTR}"
    )

    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# 📲 BLIK — krok 2 (oczekiwanie na potwierdzenie)
@router.callback_query(F.data == "blik_paid")
async def handle_blik_paid(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_confirmation)
    await callback.message.answer(PAYMENT_BLIK_STEP2_PROMPT, parse_mode="HTML")
    await callback.answer()


def _is_valid_proof(msg: Message) -> bool:
    if msg.photo:
        return True
    doc = msg.document
    if not doc:
        return False
    mime = (doc.mime_type or "").lower()
    if mime.startswith("image/"):
        return True
    if mime == "application/pdf":
        return True
    return False


@router.message(PaymentStates.waiting_for_confirmation)
async def forward_payment_confirmation(message: Message, state: FSMContext):
    if not _is_valid_proof(message):
        return await message.answer(PAYMENT_BLIK_ERR_NEED_PHOTO_OR_DOC, parse_mode="HTML")

    caption = (message.caption or "").strip()
    if len(caption) < 5:
        return await message.answer(PAYMENT_BLIK_ERR_NEED_CAPTION, parse_mode="HTML")

    data = await state.get_data()
    product_id = data.get("product_id")
    city = data.get("city", "")
    category = data.get("category", "")

    product = await get_product_by_id(product_id) if product_id else None
    product_name = product["name"] if product else "(brak)"
    base_price = float(product["price"]) if product else 0.0

    # скидка
    active_promo = await get_user_active_promo(message.from_user.id)
    final_price = base_price

    if active_promo and product and promo_applicable_for(category, city, active_promo):
        final_price, _ = apply_discount(base_price, active_promo)

    # 0. Сохраняем заказ в БД
    try:
        order_id = await create_order(
            telegram_id=message.from_user.id,
            product_id=product_id,
            city=city,
            category=category,
            price=final_price,
            payment_method="blik",
            address=caption,  # подпись пользователя с адресом
            payment_proof_message_id=message.message_id,
        )
        logger.info("🧾 Создан заказ #%s (BLIK) для %s", order_id, message.from_user.id)
    except Exception as e:
        logger.error("create_order(BLIK) failed: %s", e)
        # продолжаем, чтобы всё равно уведомить админов

    # 1. Пересылаем подтверждение всем согласным админам
    await forward_to_admins(message.bot, message)

    # 2. Текст с деталями
    discount_line = ""
    if active_promo and product and promo_applicable_for(category, city, active_promo):
        if active_promo["type"] == "percent":
            discount_line = f"\n🎟️ Kod: {active_promo['code']} (−{active_promo['value']:.0f}%) • cena: {final_price:.2f} zł"
        else:
            discount_line = f"\n🎟️ Kod: {active_promo['code']} (−{active_promo['value']:.2f} zł) • cena: {final_price:.2f} zł"
    else:
        discount_line = f"\nCena: {final_price:.2f} zł"

    details_text = (
        f"{ADMIN_ORDER_NEW_HEADER}\n"
        f"{ADMIN_ORDER_DETAILS.format(city=city, category=category, product_name=product_name, price=f'{base_price:.2f}')}"
        f"{discount_line}\n\n"
        f"📍 Adres (z podpisu):\n{caption}\n"
        f"👤 Klient: @{message.from_user.username or '-'} | ID: {message.from_user.id}"
    )
    await notify_admins(message.bot, details_text)

    await message.answer(PAYMENT_BLIK_OK, parse_mode="HTML", reply_markup=main_menu_inline_kb())
    await state.clear()


# 💵 Gotówka
@router.callback_query(F.data == "pay_cash")
async def handle_cash_payment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_cash_address)
    await callback.message.answer(PAYMENT_CASH_PROMPT, parse_mode="HTML")
    await callback.answer()


@router.message(PaymentStates.waiting_for_cash_address)
async def forward_cash_address(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city = user_data.get("city", "")
    category = user_data.get("category", "")
    product_id = user_data.get("product_id")
    product = await get_product_by_id(product_id) if product_id else {}

    base_price = float(product["price"]) if product else 0.0
    active_promo = await get_user_active_promo(message.from_user.id)
    final_price = base_price

    if active_promo and product and promo_applicable_for(category, city, active_promo):
        final_price, _ = apply_discount(base_price, active_promo)

    # 0. Сохраняем заказ в БД
    try:
        order_id = await create_order(
            telegram_id=message.from_user.id,
            product_id=product_id,
            city=city,
            category=category,
            price=final_price,
            payment_method="cash",
            address=message.text or "",
            payment_proof_message_id=None,
        )
        logger.info("🧾 Создан заказ #%s (CASH) для %s", order_id, message.from_user.id)
    except Exception as e:
        logger.error("create_order(CASH) failed: %s", e)

    # 1. Текст админу
    discount_line = ""
    if active_promo and product and promo_applicable_for(category, city, active_promo):
        if active_promo["type"] == "percent":
            discount_line = f"\n🎟️ Kod: {active_promo['code']} (−{active_promo['value']:.0f}%) • cena: {final_price:.2f} zł"
        else:
            discount_line = f"\n🎟️ Kod: {active_promo['code']} (−{active_promo['value']:.2f} zł) • cena: {final_price:.2f} zł"
    else:
        discount_line = f"\nCena: {final_price:.2f} zł"

    text = (
        f"🚗 ZAMÓWIENIE ZA GOTÓWKĘ\n\n"
        f"🧾 Produkt: {product.get('name', '')}\n"
        f"🏷️ Kategoria: {category}\n"
        f"🏙️ Miasto: {city}\n"
        f"📍 Adres: {message.text}\n"
        f"👤 Klient: @{message.from_user.username or '-'} | ID: {message.from_user.id}"
        f"{discount_line}"
    )
    await notify_admins(message.bot, text)

    await message.answer(PAYMENT_CASH_OK, parse_mode="HTML", reply_markup=main_menu_inline_kb())
    await state.clear()
