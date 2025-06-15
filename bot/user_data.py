import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent
DATA_FILE = DATA_DIR / "user_data.json"

if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump({"pairs": {}, "settings": {}}, f)

AVAILABLE_PAIRS = [
    'EUR/AUD', 'USD/JPY', 'GBP/JPY', 'CHF/JPY', 'AUD/JPY',
    'USD/CHF', 'CAD/JPY', 'GBP/CHF', 'EUR/GBP', 'CAD/CHF',
    'AUD/CAD', 'GBP/USD', 'EUR/CHF', 'EUR/CAD', 'AUD/CHF',
    'USD/CAD', 'EUR/JPY', 'EUR/USD', 'AUD/USD', 'BTC/USDT'
]

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"pairs": {}, "settings": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Функции для работы с парами
def get_pairs(user_id):
    return load_data()["pairs"].get(str(user_id), [])

def add_pair(user_id, pair):
    data = load_data()
    if "pairs" not in data:
        data["pairs"] = {}
    if str(user_id) not in data["pairs"]:
        data["pairs"][str(user_id)] = []
    if pair in AVAILABLE_PAIRS and pair not in data["pairs"][str(user_id)]:
        data["pairs"][str(user_id)].append(pair)
        save_data(data)
        return True
    return False

def remove_pair(user_id, pair):
    data = load_data()
    if pair in data["pairs"].get(str(user_id), []):
        data["pairs"][str(user_id)].remove(pair)
        save_data(data)
        return True
    return False

def add_all_pairs(user_id):
    data = load_data()
    data["pairs"][str(user_id)] = AVAILABLE_PAIRS.copy()
    save_data(data)
    return True

def remove_all_pairs(user_id):
    data = load_data()
    if str(user_id) in data["pairs"]:
        data["pairs"][str(user_id)] = []
        save_data(data)
        return True
    return False

# Функции для работы с настройками
def get_user_settings(user_id):
    data = load_data()
    return data["settings"].get(str(user_id), {"rsi_period": 14})

def update_user_settings(user_id, settings):
    data = load_data()
    if "settings" not in data:
        data["settings"] = {}
    data["settings"][str(user_id)] = settings
    save_data(data)

def get_available_pairs():
    return sorted(AVAILABLE_PAIRS)