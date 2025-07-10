# Настройка логирования в файл bot.log и в консоль
import logging

logging.basicConfig(
    level=logging.INFO, # Уровень логирования(можно DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)s] %(message)s',  # Формат логов
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]

)
# Создание логгера
logger = logging.getLogger(__name__)