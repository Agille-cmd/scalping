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
    """Выбор API провайдера с учётом доступности"""
    active_providers = [p for p in API_PROVIDERS if p.get('active', True)]
    if not active_providers:
        raise ValueError("Нет доступных API провайдеров")
    return active_providers[0]  # Возвращаем провайдера с наивысшим приоритетом

def handle_api_error(provider, error):
    """Обработка ошибок API"""
    print(f"API Error ({provider['name']}): {error}")
    if "limit exceeded" in str(error).lower():
        provider['active'] = False
        print(f"Temporarily disabling {provider['name']} due to rate limit")

def get_fx_data(symbol, interval='1min'):
    """Получение данных с API с обработкой ошибок"""
    try:
        # Проверка и форматирование символа
        if '/' not in symbol:
            raise ValueError("Символ должен содержать '/' (например EUR/USD)")
            
        from_curr, to_curr = symbol.split('/')
        
        provider = get_api_provider()
        if provider['name'] == 'twelvedata':
            # Формат для TwelveData
            pair = f"{from_curr}{to_curr}"
            url = f"{provider['url']}/time_series?symbol={pair}&interval={interval}&apikey={provider['key']}"
        else:
            # Формат для Polygon
            url = f"{provider['url']}/v1/historic/forex/{from_curr}/{to_curr}/latest?apiKey={provider['key']}"
        
        response = requests.get(url)
        response.raise_for_status()  # Проверка HTTP ошибок
        
        data = response.json()
        
        # TwelveData проверка
        if provider['name'] == 'twelvedata' and 'values' not in data:
            raise ValueError(f"TwelveData error: {data.get('message', 'Unknown error')}")
        
        # Polygon проверка
        if provider['name'] == 'polygon' and 'ticks' not in data:
            raise ValueError(f"Polygon error: {data.get('error', 'Unknown error')}")
        
        # Форматирование данных
        if provider['name'] == 'twelvedata':
            return {item['datetime']: float(item['close']) for item in data['values']}
        else:
            return {tick['t']: tick['c'] for tick in data['ticks']}
            
    except requests.exceptions.RequestException as re:
        print(f"Request error: {str(re)}")
        return None
    except ValueError as ve:
        print(f"Value error: {str(ve)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
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