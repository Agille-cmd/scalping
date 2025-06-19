# data.py — минимизирован, только необходимые настройки
import os
from pathlib import Path
from dotenv import load_dotenv

# Явно указываем путь к .env
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print(f"✅ .env loaded from {ENV_PATH}")
else:
    print(f"⚠️ Warning: .env file not found at {ENV_PATH}")

# Получаем токен с проверкой
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError(
        "TELEGRAM_TOKEN not found in environment variables. "
        "Please check your .env file in project root directory."
    )

# Доступные торговые пары
AVAILABLE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD",
    "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/CAD",
    "AUD/CAD", "CAD/JPY", "CHF/JPY", "EUR/AUD",
    "EUR/NZD", "GBP/CAD", "GBP/CHF", "NZD/JPY"
]

# Доступные интервалы
AVAILABLE_INTERVALS = ["1min", "5min", "15min", "30min", "1h", "4h", "1day"]