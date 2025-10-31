# utils/logger.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # Логирование в файл
        logging.StreamHandler()
    ]

)
logger = logging.getLogger(__name__)