# tg-sales-bot/bot.py
# Точка входа для запуска Telegram бота
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db, close_db
from database.crud import (
    create_users_table,
    create_products_table,
    create_orders_table,
    create_admin_consents_table,
    create_promo_tables,
    create_settings_table,

    # словари
    create_cities_table,
    create_categories_table,
    create_city_categories_table,
)

from handlers.user import (
    start_router,
    menu_router,
    catalog_router,
    payment_router,
    navigation_router,
    history_router,
)

from handlers.admin import (
    access_router,
    add_product_router,
    list_products_router,
    edit_product_router,
    admin_menu_router,
    orders_router,
    promos_router,
    consents_router,
    pages_router,
    dicts_router,
)

from utils.logger import logger


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    logger.info("Запуск бота...")

    # База и таблицы
    await init_db()
    await create_users_table()
    await create_products_table()
    await create_orders_table()
    await create_admin_consents_table()
    await create_promo_tables()
    await create_settings_table()

    # Справочники (без автосидов!)
    await create_cities_table()
    await create_categories_table()
    await create_city_categories_table()

    # Роутеры
    dp.include_routers(
        start_router,
        menu_router,
        catalog_router,
        payment_router,
        navigation_router,
        history_router,

        access_router,
        add_product_router,
        list_products_router,
        edit_product_router,
        orders_router,
        admin_menu_router,
        promos_router,
        pages_router,
        consents_router,
        dicts_router,
    )

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logger.info("Бот остановлен, база данных закрыта.")


if __name__ == "__main__":
    asyncio.run(main())
