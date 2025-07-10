# Этот файл загружает переменные окружения из .env файла и предоставляет их для использования в приложении.
from dotenv import load_dotenv
import os

# загрузка переменных окружения из .env файла
load_dotenv()

# получаем токен бота и строку подключения к базе данных
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
