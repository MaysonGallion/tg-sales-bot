# tg-sales-bot/handlers/admin/access.py
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS, ADMIN_PASSWORD
from states.admin_states import AdminAccessState

from keyboards.inline.admin import admin_main_kb, admin_legal_accept_kb
from database.crud import has_consented
from messages.pl import LEGAL_CONSENT_VERSION, LEGAL_CONSENT_PROMPT

router = Router()

async def _safe_edit_text(msg: types.Message, text: str, reply_markup=None, parse_mode: str | None = "HTML"):
    try:
        await msg.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except TelegramBadRequest:
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)

@router.message(F.text == "/@sklad45")
async def request_admin_access(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminAccessState.waiting_for_password)
    await message.answer("Poproszę hasło admina:")

@router.message(AdminAccessState.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    if (message.text or "").strip() != ADMIN_PASSWORD:
        return await message.answer("❌ Hasło niepoprawne, spróbuj ponownie")

    await state.clear()

    admin_id = message.from_user.id
    if not await has_consented(admin_id, LEGAL_CONSENT_VERSION):
        # тут невозможно «редактировать текущее» (это ответ на текст с паролем),
        # поэтому отправляем одно сообщение с согласием
        await message.answer(LEGAL_CONSENT_PROMPT, parse_mode="HTML", reply_markup=admin_legal_accept_kb())
        return

    await message.answer("✅ Dostęp przyznany.\n\n🛠️ Panel admina:", reply_markup=admin_main_kb())
