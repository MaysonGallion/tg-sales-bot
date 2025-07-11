# Обработчик команды /start: регистрация пользователя и приветствие
from aiogram import types, Router
from aiogram.filters import CommandStart
from database.crud import create_or_get_user
from keyboards.inline import main_menu_inline_kb
from utils.logger import logger

# Создаем роутер для обработки команды /start
router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    user = message.from_user

    # Регистрация пользователя в базе данных
    await create_or_get_user(
        telegram_id=user.id,
        first_name=user.first_name or "",
        username=user.username or "",
        language_code=user.language_code or "",
    )

    # Логируем информацию о пользователе
    logger.info(f"Nowy 👤 Użytkownik uruchomił bota: {user.id} - {user.full_name} ({user.username})")

    # Отправляем приветственное сообщение с кнопкой главного меню
    text = (
        f"Cześć, {user.first_name}!\n"
        f"Witamy w naszym sklepie.\n"
        f"Wybierz opcję z menu poniżej 👇"
    )
    await message.answer(text=text, reply_markup=main_menu_inline_kb())
