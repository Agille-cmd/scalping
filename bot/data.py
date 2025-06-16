import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

TELEGRAM_TOKEN = config['telegram_token']
ALPHA_VANTAGE_API_KEY = config['alpha_vantage_api_key']

AVAILABLE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", 
    "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/CAD",
    "AUD/CAD", "CAD/JPY", "CHF/JPY", "EUR/AUD",
    "EUR/NZD", "GBP/CAD", "GBP/CHF", "NZD/JPY"
]