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
        if city:
            query = """
                SELECT * FROM products 
                WHERE active = TRUE 
                AND LOWER(category) = LOWER($1)
                AND (city ILIKE $2 OR city = 'Wszystkie')
            """
            return await conn.fetch(query, category, city)
        else:
            query = """
                SELECT * FROM products 
                WHERE active = TRUE 
                AND LOWER(category) = LOWER($1)
            """
            return await conn.fetch(query, category)



async def get_product_by_id(product_id: int):
    async with db.pool.acquire() as conn:
        query = """
            SELECT * FROM products 
            WHERE id = $1 AND active = TRUE
        """
        return await conn.fetchrow(query, product_id)
