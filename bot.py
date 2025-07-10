# Точка входа для запуска Telegram бота
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from database.db import init_db, close_db
from database.crud import create_users_table
from handlers.user import start_router
from utils.logger import logger


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    logger.info("Запуск бота...")

    # Подключение к базе и создание таблиц
    await init_db()
    await create_users_table()

    # Подключаем пользовательский роутер
    dp.include_router(start_router)

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logger.info("Бот остановлен, база данных закрыта.")

if __name__ == "__main__":
    asyncio.run(main())
