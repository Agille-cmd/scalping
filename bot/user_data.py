import json
import os
from pathlib import Path

DATA_FILE = Path(__file__).parent / "user_data.json"

# Инициализация файла данных
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump({"pairs": {}, "settings": {}}, f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_pair(user_id, pair):
    data = load_data()
    if str(user_id) not in data["pairs"]:
        data["pairs"][str(user_id)] = []
    if pair not in data["pairs"][str(user_id)]:
        data["pairs"][str(user_id)].append(pair)
        save_data(data)
        return True
    return False

def remove_pair(user_id, pair):
    data = load_data()
    if str(user_id) in data["pairs"] and pair in data["pairs"][str(user_id)]:
        data["pairs"][str(user_id)].remove(pair)
        save_data(data)
        return True
    return False

def clear_pairs(user_id):
    data = load_data()
    if str(user_id) in data["pairs"]:
        data["pairs"][str(user_id)] = []
        save_data(data)
        return True
    return False

def set_rsi_period(user_id, period):
    data = load_data()
    if "settings" not in data:
        data["settings"] = {}
    data["settings"][str(user_id)] = {"rsi_period": period}
    save_data(data)

def get_rsi_period(user_id):
    data = load_data()
    return data["settings"].get(str(user_id), {}).get("rsi_period", 14)

def get_user_pairs(user_id):
    data = load_data()
    return data["pairs"].get(str(user_id), [])