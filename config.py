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

def load_config() -> bool:
    """Загружает конфигурацию из .env файла и проверяет обязательные переменные."""
    try:
        # Пробуем загрузить .env файл
        if not load_dotenv():
            logger.warning(".env файл не найден, используются переменные окружения")
        
        # Проверяем обязательные переменные
        required_vars = ['TELEGRAM_TOKEN', 'TWELVEDATA_API_KEYS']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {str(e)}")
        return False

# Основные настройки
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN', '')
TWELVEDATA_API_KEYS: List[str] = [
    key.strip() for key in os.getenv('TWELVEDATA_API_KEYS', '').split(',') if key.strip()
]

# Валютные пары для торговли
ALLOWED_PAIRS: List[str] = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD",
    "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY"
]

# Временные параметры
ACTIVE_TRADING_HOURS: List[tuple] = [(9, 12), (14, 17)]  # GMT
CANDLE_INTERVAL: str = "1min"  # Таймфрейм для данных

# Параметры стратегии
RSI_PERIOD: int = 7
RSI_OVERBOUGHT: int = 80
RSI_OVERSOLD: int = 20
EMA_FAST: int = 20
EMA_SLOW: int = 50
BB_PERIOD: int = 20
BB_STDDEV: int = 2

# Проверяем загрузку конфигурации при импорте
if not load_config():
    raise RuntimeError("Не удалось загрузить конфигурацию. Проверьте .env файл.")

# Дополнительные проверки
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не может быть пустым")

if not TWELVEDATA_API_KEYS:
    raise ValueError("Не указаны ключи для TwelveData API")

logger.info("Конфигурация успешно загружена")
