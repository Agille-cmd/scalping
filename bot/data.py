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

def check_api_keys():
    """Проверка валидности API ключей при старте"""
    for provider in API_PROVIDERS:
        if not provider.get('key'):
            print(f"⚠️ Missing API key for {provider['name']}")
            provider['active'] = False

# Остальные настройки
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

# Доступные торговые пары
AVAILABLE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD",
    "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/CAD",
    "AUD/CAD", "CAD/JPY", "CHF/JPY", "EUR/AUD",
    "EUR/NZD", "GBP/CAD", "GBP/CHF", "NZD/JPY"
]

# Для TwelveData нужно использовать формат без '/'
TD_PAIRS = [p.replace('/', '') for p in AVAILABLE_PAIRS]

# Доступные временные интервалы
AVAILABLE_INTERVALS = ["1min", "5min", "15min", "30min", "1h", "4h", "1day"]
API_ENDPOINTS = {
    'twelvedata': {
        'forex': '/time_series?symbol={pair}&interval={interval}&apikey={key}',
        'stocks': '/stocks?symbol={symbol}&interval={interval}&apikey={key}'
    },
    'polygon': {
        'forex': '/v1/historic/forex/{from_curr}/{to_curr}/{date}?apiKey={key}',
        'stocks': '/v2/aggs/ticker/{symbol}/range/1/{interval}/{start}/{end}?apiKey={key}'
    }
}