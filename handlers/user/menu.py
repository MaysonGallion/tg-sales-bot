# tg_sales_bot/handlers/user/menu.py
from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.logger import logger

router = Router()



# 🧭 Главное меню (кроме zakupów)
@router.callback_query(lambda c: c.data.startswith("menu_") and c.data != "menu_zakupy")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    logger.info(f"➡️ {callback.from_user.id} wybrał z menu głównego: {data}")

    if data == "menu_historia":
        await callback.message.answer("📖 Tutaj będzie historia zamówień.")
    elif data == "menu_bonus":
        await callback.message.answer("🎁 Wprowadź swój kod promocyjny.")
    elif data == "menu_regulamin":
        await callback.message.answer("📜 Regulamin sklepu...")
    elif data == "menu_pomoc":
        await callback.message.answer("💬 Skontaktuj się z obsługą klienta.")

    await callback.answer()