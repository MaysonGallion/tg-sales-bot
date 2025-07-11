# SQL-запросы для создания таблиц в базе данных

# Таблица users хранит информацию о пользователях

CREATE_USERS_TABLE ="""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,                  -- Уникальный идентификатор пользователя
    telegram_id BIGINT UNIQUE,              -- Уникальный идентификатор пользователя в Telegram
    first_name VARCHAR(100),                -- Имя пользователя
    username VARCHAR(100),                  -- Имя пользователя в Telegram
    language_code VARCHAR(10),              -- Языковой код пользователя
    order_count INTEGER DEFAULT 0,          -- Количество заказов пользователя
    created_at TIMESTAMP DEFAULT NOW()      -- Дата и время создания записи
);
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,                  -- Уникальный идентификатор продукта
    name VARCHAR(255) NOT NULL,             -- Название продукта
    description TEXT,                       -- Описание продукта
    price NUMERIC(10, 2) NOT NULL,          -- Цена продукта
    category VARCHAR(100),                  -- Категория продукта
    photo_url TEXT,                         -- URL фотографии продукта
    city VARCHAR(50) DEFAULT 'Wszystkie',   -- Город, в котором доступен продукт
    active BOOLEAN DEFAULT TRUE,            -- Статус активности продукта
    created_at TIMESTAMP DEFAULT NOW()      -- Дата и время создания записи
);
"""