# tg_sales_bot/handlers/user/menu.py

from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline.menu import main_menu_inline_kb
from utils.logger import logger
from states.user_states import OrderStates
from keyboards.inline.order import city_selection_kb, category_selection_kb

router = Router()


# 🧭 Главное меню (обрабатываем все callback'и кроме zakupów)
@router.callback_query(lambda c: c.data.startswith("menu_") and c.data != "menu_zakupy")
async def handle_main_menu(callback: CallbackQuery):
    data = callback.data
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: {data}")

    if data == "menu_katalog":
        await callback.message.answer("📦 Przeglądaj nasz katalog produktów.")
    elif data == "menu_historia":
        await callback.message.answer("📖 Tutaj będzie historia zamówień.")
    elif data == "menu_bonus":
        await callback.message.answer("🎁 Wprowadź swój kod promocyjny.")
    elif data == "menu_regulamin":
        await callback.message.answer("📜 Regulamin sklepu...")
    elif data == "menu_pomoc":
        await callback.message.answer("💬 Skontaktuj się z obsługą klienta.")

    await callback.answer()


# 🏠 Возврат в главное меню
@router.callback_query(lambda c: c.data == "to_main")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # сбрасываем состояние FSM
    logger.info(f"🏠 {callback.from_user.id} wrócił do menu głównego")

    await callback.message.edit_text(
        "🏠 Wróciłeś do menu głównego. Wybierz opcję:",
        reply_markup=main_menu_inline_kb()
    )
    await callback.answer()


# 🛒 Начало покупки — выбор города
@router.callback_query(lambda c: c.data == "menu_zakupy")
async def zakupy_step_1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.choosing_city)

    logger.info(f"🛒 {callback.from_user.id} rozpoczął zakupy (wybór miasta)")

    await callback.message.edit_text(
        "🗺️ Wybierz miasto dostawy:",
        reply_markup=city_selection_kb()
    )
    await callback.answer()


# 📍 Обработка выбранного города → категория
@router.callback_query(lambda c: c.data.startswith("city_"))
async def handle_city_selection(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_")[1].capitalize()
    await state.update_data(city=city)

    await state.set_state(OrderStates.choosing_category)

    logger.info(f"📍 {callback.from_user.id} wybrał miasto: {city}")

    await callback.message.edit_text(
        f"📦 Wybrałeś miasto: {city}\nTeraz wybierz kategorię:",
        reply_markup=category_selection_kb()
    )
    await callback.answer()
