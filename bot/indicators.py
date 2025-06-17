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
    """Улучшенная функция получения данных с обработкой ошибок"""
    try:
        # Проверка и форматирование символа
        if '/' not in symbol:
            raise ValueError(f"Invalid symbol format: {symbol}. Use 'EUR/USD' format")
        
        from_curr, to_curr = symbol.split('/')
        provider = get_api_provider()
        
        # TwelveData запрос
        if provider['name'] == 'twelvedata':
            url = f"{provider['url']}/time_series?symbol={from_curr}{to_curr}&interval={interval}&apikey={provider['key']}&outputsize=100&format=JSON"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Проверка ответа
            if 'code' in data and data['code'] == 429:
                print("⚠️ TwelveData rate limit reached")
                provider['active'] = False
                return None
                
            if 'values' not in data:
                error_msg = data.get('message', 'No price data in response')
                print(f"TwelveData error: {error_msg}")
                return None
                
            # Преобразование данных
            return {
                item['datetime']: float(item['close'])
                for item in data['values']
                if 'close' in item
            }
        
        # Polygon запрос
        else:
            url = f"{provider['url']}/v1/historic/forex/{from_curr}/{to_curr}/latest?apiKey={provider['key']}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'ticks' not in data:
                print(f"Polygon error: {data.get('error', 'Invalid response')}")
                return None
                
            return {tick['t']: tick['c'] for tick in data['ticks']}
            
    except requests.exceptions.RequestException as re:
        print(f"Request failed: {str(re)}")
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