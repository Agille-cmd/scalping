import os
from dotenv import load_dotenv
from typing import List, Tuple
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка .env файла
load_dotenv('/root/scalping/.env')

# Основные настройки
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN', '')
TWELVEDATA_API_KEYS: List[str] = [
    key.strip() for key in os.getenv('TWELVEDATA_API_KEYS', '').split(',') if key.strip()
]

# Торговые настройки
ALLOWED_PAIRS: List[str] = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD",
    "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY"
]

# Временные параметры
ACTIVE_TRADING_HOURS: List[Tuple[int, int]] = [
    (9, 12),  # Лондонская сессия
    (14, 17)  # Нью-Йоркская сессия
]

# Параметры индикаторов
RSI_PERIOD: int = 7
EMA_FAST: int = 20
EMA_SLOW: int = 50
BB_PERIOD: int = 20
BB_STDDEV: int = 2

# Проверка конфигурации
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не может быть пустым")

if not TWELVEDATA_API_KEYS:
    raise ValueError("Не указаны ключи для TwelveData API")

logger.info("Конфигурация успешно загружена")
