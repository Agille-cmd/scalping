import os
from dotenv import load_dotenv
from typing import List
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка .env файла
if not load_dotenv('/root/scalping/.env'):
    logger.warning("Не удалось загрузить .env файл, пробуем переменные окружения")

# Основные настройки
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN', '')
TWELVEDATA_API_KEYS: List[str] = [
    key.strip() for key in os.getenv('TWELVEDATA_API_KEYS', '').split(',') if key.strip()
]

# Валютные пары
ALLOWED_PAIRS: List[str] = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD",
    "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY"
]

# Проверка токена
if not TELEGRAM_TOKEN:
    logger.error("Токен Telegram не найден. Проверьте:")
    logger.error("1. Существует ли файл /root/scalping/.env")
    logger.error("2. Содержит ли он TELEGRAM_TOKEN=ваш_токен")
    logger.error("3. Установлены ли права 600 на .env файл")
    exit(1)

logger.info("Конфигурация успешно загружена")
