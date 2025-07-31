# tg-sales-bot/handlers/user/payment.py
from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.user_states import PaymentStates
from database.crud import get_product_by_id
from config import ADMIN_ID

router = Router()

# 💳 Выбор метода оплаты
@router.callback_query(lambda c: c.data == "choose_payment")
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Gotówka na miejscu", callback_data="pay_cash")],
        [InlineKeyboardButton(text="📲 BLIK na numer", callback_data="pay_blik")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="back_to_products")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    await callback.message.delete()
    await callback.message.answer(
        "💳 <b>Wybierz metodę płatności:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# Оплата BLIK — шаг 1
@router.callback_query(lambda c: c.data == "pay_blik")
async def handle_blik_payment(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Opłacone, przejdź dalej", callback_data="blik_paid")],
        [InlineKeyboardButton(text="🏠 Menu główne", callback_data="to_main")]
    ])

    await callback.message.answer(
        "📲 <b>Numer BLIK:</b> 123456789\n\n"
        "➡️ Wykonaj przelew BLIK i zrób <b>zrzut ekranu potwierdzenia</b>.\n"
        "⚠️ <b>WAŻNE:</b> zrzut ekranu wyślij <b>jako zdjęcie</b>.\n"
        "📝 W podpisie zdjęcia wpisz <b>adres dostawy</b> (np. Gdańsk, ul. Długa 5/2)\n\n"
        "❗ <b>Nie wysyłaj zdjęcia TERAZ.</b> Najpierw kliknij przycisk poniżej „Opłacone, przejdź dalej”.\n"
        "📩 Dopiero wtedy bot poprosi Cię o przesłanie zdjęcia i adresа.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# Оплата BLIK — шаг 2: подтверждение
@router.callback_query(lambda c: c.data == "blik_paid")
async def handle_blik_paid(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_confirmation)
    await callback.message.answer(
        "📤 Wyślij teraz <b>zrzut ekranu potwierdzenia przelewu</b> jako zdjęcie.\n"
        "📝 <b>Adres dostawy</b> podaj w podpisie do zdjęcia.\n\n"
        "🚚 Po przesłaniu przekażemy dane do realizacji zamówienia.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentStates.waiting_for_confirmation)
async def forward_payment_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    city = data.get("city")
    category = data.get("category")

    product = await get_product_by_id(product_id)

    # 1. Пересылаем скрин оплаты
    await message.forward(ADMIN_ID)

    # 2. Информация о заказе
    details = (
        f"🛒 <b>Nowe zamówienie:</b>\n"
        f"🏙️ Miasto: <b>{city}</b>\n"
        f"📦 Kategoria: <b>{category}</b>\n"
        f"🛍️ Produkt: <b>{product['name']}</b>\n"
        f"💰 Cena: <b>{product['price']} zł</b>"
    )

    await message.bot.send_message(ADMIN_ID, details, parse_mode="HTML")
    await message.answer("✅ Twoje dane zostały przesłane. Dziękujemy!")
    await state.clear()


# Оплата наличными
@router.callback_query(lambda c: c.data == "pay_cash")
async def handle_cash_payment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_cash_address)
    await callback.message.answer(
        "📦 Podaj <b>adres dostawy</b> (np. Gdańsk, ul. Długa 5/2).\n\n"
        "💡 Uwaga: kierowca nie wydaje reszty. Przygotuj odliczoną kwotę.\n"
        "Jeśli zapłacisz więcej — problemu nie będzie. 😊",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentStates.waiting_for_cash_address)
async def forward_cash_address(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city = user_data.get("city", "")
    category = user_data.get("category", "")
    product_id = user_data.get("product_id")
    product = await get_product_by_id(product_id) if product_id else {}

    text = (
        f"🚗 ZAMÓWIENIE ZA GOTÓWKĘ\n\n"
        f"🧾 Produkt: {product.get('name', '')}\n"
        f"🏷️ Kategoria: {category}\n"
        f"🏙️ Miasto: {city}\n"
        f"📍 Adres: {message.text}\n"
        f"👤 Klient: @{message.from_user.username} | ID: {message.from_user.id}"
    )

    await message.bot.send_message(chat_id=ADMIN_ID, text=text)
    await message.answer("✅ Adres został zapisany. Dziękujemy za zamówienie!")
    await state.clear()
