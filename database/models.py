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