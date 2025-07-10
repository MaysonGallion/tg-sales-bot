# Функции для работы с таблицей users
import database.db as db
from database.models import CREATE_USERS_TABLE
from utils.logger import logger


# Создание таблицы users, если она не существует
async def create_users_table():
    async with db.pool.acquire() as connection:
        await connection.execute(CREATE_USERS_TABLE)
        logger.info("✅ Таблица users успешно создана или уже существует.")


# Добавление нового пользователя в таблицу users(или игнор при повторе)
async def create_or_get_user(telegram_id: int, first_name: str, username: str, language_code: str):
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, first_name, username, language_code)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO NOTHING;
            """,
            telegram_id, first_name, username, language_code
        )
        logger.info(f"👤 Пользователь {telegram_id} зарегистрирован (или уже был).")
