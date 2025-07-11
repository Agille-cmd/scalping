import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Токен бота
TWELVEDATA_API_KEYS = os.getenv("TWELVEDATA_API_KEYS", "").split(",")  # Список API-ключей
ALLOWED_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD",
    "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY"
]
ACTIVE_TRADING_HOURS = [(9, 12), (14, 17)]  # GMT
