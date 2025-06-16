import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)

TELEGRAM_TOKEN = config['telegram_token']
ALPHA_VANTAGE_API_KEY = config['alpha_vantage_api_key']

AVAILABLE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY", "EUR/GBP"
]