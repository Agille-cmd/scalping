import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройки API
API_PROVIDERS = [
    {
        'name': 'twelvedata',
        'key': os.getenv('TWELVE_DATA_KEY'),
        'url': 'https://api.twelvedata.com',
        'limits': {'day': 800, 'minute': 8},
        'priority': 1
    },
    {
        'name': 'polygon',
        'key': os.getenv('POLYGON_KEY'),
        'url': 'https://api.polygon.io',
        'limits': {'day': 200, 'minute': 5},
        'priority': 2
    }
]

# Токен бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Доступные торговые пары
AVAILABLE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD",
    "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/CAD",
    "AUD/CAD", "CAD/JPY", "CHF/JPY", "EUR/AUD",
    "EUR/NZD", "GBP/CAD", "GBP/CHF", "NZD/JPY"
]

# Доступные временные интервалы
AVAILABLE_INTERVALS = ["1min", "5min", "15min", "30min", "60min", "daily"]