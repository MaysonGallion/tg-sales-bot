import database.db as db  # импортируем весь модуль db.py
from database.models import CREATE_PRODUCTS_TABLE
from utils.logger import logger


# Создание таблицы products
async def create_products_table():
    async with db.pool.acquire() as conn:  # правильно — db.pool
        await conn.execute(CREATE_PRODUCTS_TABLE)
        logger.info("📦 Таблица products создана или уже существует.")


# Получение товаров по категории и городу (если задан город)
async def get_products(category: str, city: str = None):
    async with db.pool.acquire() as conn:
        if city and city.lower() != "wszystkie":
            query = """
                SELECT * FROM products 
                WHERE active = TRUE AND category = $1 AND city = $2
            """
            return await conn.fetch(query, category, city)
        else:
            query = """
                SELECT * FROM products 
                WHERE active = TRUE AND category = $1
            """
            return await conn.fetch(query, category)
