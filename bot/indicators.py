import requests
import pandas as pd
import time
from datetime import datetime
from random import choice
from bot.data import API_PROVIDERS, AVAILABLE_PAIRS
from bot.user_data import get_rsi_period

# Кэширование на 5 минут (как в исходной версии)
rsi_cache = {}
CACHE_TIME = 300

def get_api_provider():
    """Выбираем случайный доступный провайдер"""
    active_providers = [p for p in API_PROVIDERS if p.get('active', True)]
    if not active_providers:
        raise Exception("No active API providers available")
    return choice(sorted(active_providers, key=lambda x: x['priority']))

def handle_api_error(provider, error):
    """Обработка ошибок API"""
    print(f"API Error ({provider['name']}): {error}")
    if "limit exceeded" in str(error).lower():
        provider['active'] = False
        print(f"Temporarily disabling {provider['name']} due to rate limit")

def get_fx_data(symbol, interval='1min'):
    """Получение данных с ротацией провайдеров"""
    from_symbol, to_symbol = symbol.split('/')
    
    for attempt in range(3):
        provider = get_api_provider()
        try:
            if provider['name'] == 'twelvedata':
                url = f"{provider['url']}/time_series?symbol={from_symbol}{to_symbol}&interval={interval}&apikey={provider['key']}"
                response = requests.get(url)
                data = response.json()
                if 'values' not in data:
                    raise Exception(data.get('message', 'Invalid response'))
                return {k['datetime']: float(k['close']) for k in data['values']}
            
            elif provider['name'] == 'polygon':
                url = f"{provider['url']}/v1/historic/forex/{from_symbol}/{to_symbol}/{datetime.now().strftime('%Y-%m-%d')}?apiKey={provider['key']}"
                response = requests.get(url)
                data = response.json()
                if 'ticks' not in data:
                    raise Exception(data.get('error', 'Invalid response'))
                return {k['t']: k['c'] for k in data['ticks']}
                
        except Exception as e:
            handle_api_error(provider, e)
            time.sleep(1)
    
    raise Exception("All API providers failed")

def calculate_rsi(prices, period=14):
    """Расчет RSI из цен"""
    series = pd.Series(prices)
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs)).iloc[-1].round(2)

def get_rsi(user_id, symbol):
    """Основная функция получения RSI"""
    if symbol not in AVAILABLE_PAIRS:
        return None
        
    cache_key = (user_id, symbol)
    if cache_key in rsi_cache:
        value, timestamp = rsi_cache[cache_key]
        if time.time() - timestamp < CACHE_TIME:
            return value
    
    try:
        prices = get_fx_data(symbol)
        rsi_value = calculate_rsi(prices, get_rsi_period(user_id))
        rsi_cache[cache_key] = (rsi_value, time.time())
        return rsi_value
    except Exception as e:
        print(f"Error getting RSI for {symbol}: {str(e)}")
        return None