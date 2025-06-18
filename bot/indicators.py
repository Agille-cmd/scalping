import requests
import pandas as pd
import time
from datetime import datetime
from random import choice
from bot.data import API_PROVIDERS, AVAILABLE_PAIRS
from bot.user_data import get_rsi_period, get_time_interval

# Кэширование на 5 минут (как в исходной версии)
rsi_cache = {}
CACHE_TIME = 300

def get_api_provider():
    active_providers = sorted(
        [p for p in API_PROVIDERS if p.get('active', True)],
        key=lambda x: x['priority']
    )
    if not active_providers:
        raise ValueError("Нет доступных API провайдеров")
    return active_providers[0]


def handle_api_error(provider, error):
    """Обработка ошибок API"""
    print(f"API Error ({provider['name']}): {error}")
    if "limit exceeded" in str(error).lower():
        provider['active'] = False
        print(f"Temporarily disabling {provider['name']} due to rate limit")

def get_fx_data(symbol, interval='1min'):
    """Получение исторических данных по валютной паре с обработкой всех ошибок"""
    try:
        # Проверка формата пары
        if '/' not in symbol:
            raise ValueError(f"❌ Неверный формат символа: {symbol}. Используй формат 'EUR/USD'")
        
        from_curr, to_curr = symbol.split('/')
        provider = get_api_provider()
        
        print(f"📡 Попытка запроса данных: {symbol} ({interval}) через {provider['name']}")

        # ==== TwelveData ====
        if provider['name'] == 'twelvedata':
            url = f"{provider['url']}/time_series"
            params = {
                "symbol": f"{from_curr}{to_curr}",
                "interval": interval,
                "apikey": provider["key"],
                "outputsize": 100,
                "format": "JSON"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            # Обработка ошибок
            if response.status_code != 200 or "values" not in data:
                print(f"⚠️ TwelveData error: {data.get('message', 'Нет данных')}")
                provider['active'] = False
                return None
            
            return {
                item['datetime']: float(item['close'])
                for item in data['values']
                if 'close' in item
            }

        # ==== Polygon.io ====
        elif provider['name'] == 'polygon':
            url = f"{provider['url']}/v1/historic/forex/{from_curr}/{to_curr}/latest"
            params = {
                "apiKey": provider["key"]
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if response.status_code != 200 or 'ticks' not in data:
                print(f"⚠️ Polygon error: {data.get('error', 'Нет данных')}")
                provider['active'] = False
                return None

            return {
                tick['t']: tick['c'] for tick in data['ticks']
            }

        else:
            raise ValueError(f"❌ Неизвестный API-провайдер: {provider['name']}")

    except requests.exceptions.RequestException as re:
        print(f"🌐 Ошибка запроса: {str(re)}")
        provider['active'] = False
        return None
    except Exception as e:
        print(f"💥 Неожиданная ошибка в get_fx_data: {str(e)}")
        return None


def calculate_rsi(prices, period=14):
    """Расчёт RSI из цен с обработкой ошибок"""
    try:
        series = pd.Series(prices)
        delta = series.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi.iloc[-1], 2)
        
    except Exception as e:
        print(f"Error in calculate_rsi: {str(e)}")
        return None

def get_rsi(user_id, symbol):
    """Основная функция для получения RSI с обработкой ошибок"""
    try:
        # Проверка допустимости символа
        if symbol not in AVAILABLE_PAIRS:
            raise ValueError(f"Неверная валютная пара: {symbol}")

        # Получаем данные
        interval = get_time_interval(user_id)
        prices = get_fx_data(symbol, interval)
        
        if not prices:
            raise ValueError("Не удалось получить данные о ценах")

        # Рассчитываем RSI
        period = get_rsi_period(user_id)
        rsi_value = calculate_rsi(prices, period)
        
        if rsi_value is None:
            raise ValueError("Ошибка расчёта RSI")

        return rsi_value
        
    except ValueError as ve:
        print(f"ValueError in get_rsi: {str(ve)}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_rsi: {str(e)}")
        return None