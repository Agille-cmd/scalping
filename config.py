import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

TELEGRAM_TOKEN = os.getenv("8189844575:AAFX5CUov29I-mokX6pGAn2DUi_7uGLh7EY") 
TWELVEDATA_API_KEYS = os.getenv("TWELVEDATA_API_KEYS", "").split("08bd1eecd7c646e9948af6369a176ab3, afe8679ec82040308b9fcf49595fb12f")
ALLOWED_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD",
    "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY"
]
ACTIVE_TRADING_HOURS = [(9, 12), (14, 17)]  # GMT
