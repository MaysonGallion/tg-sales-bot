# Устанавливаем асинхронное подключение к PostgreSQL с помощью asyncpg
import asyncpg
from config import DATABASE_URL
from utils.logger import logger

# Глобальная переменнная для пула соединений
pool = None


# Инициализация пула подключений к базе данных
async def init_db():
    global pool
    logger.info("🔌 Подключение к базе данных...")
    pool = await asyncpg.create_pool(DATABASE_URL)
    logger.info("✅ Подключение к базе данных успешно установлено.")


# Закрытие пула при завершении работы бота
async def close_db():
    global pool
    if pool:
        logger.info("🔌 Закрытие пула подключений к базе данных...")
        await pool.close()
        logger.info("✅ Пул подключений к базе данных закрыт.")
    else:
        logger.warning("⚠️ Пул подключений к базе данных уже закрыт или не инициализирован.")
