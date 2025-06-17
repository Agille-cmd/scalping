import requests
import pandas as pd
import time
from bot.data import ALPHA_VANTAGE_API_KEY
from bot.user_data import get_rsi_period, get_time_interval

rsi_cache = {}
CACHE_TIME = 300  # 5 минут кэширования

def get_rsi(user_id, symbol):
    cache_key = (user_id, symbol, get_time_interval(user_id))
    if cache_key in rsi_cache:
        value, timestamp = rsi_cache[cache_key]
        if time.time() - timestamp < CACHE_TIME:
            return value
    
    try:
        from_symbol, to_symbol = symbol.split('/')
        interval = get_time_interval(user_id)
        
        # Формируем URL в зависимости от интервала
        if interval == "daily":
            url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
            data_key = "Time Series FX (Daily)"
        else:
            url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_symbol}&to_symbol={to_symbol}&interval={interval}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
            data_key = f"Time Series FX ({interval})"
        
        response = requests.get(url)
        data = response.json()
        
        # Проверяем наличие ошибки
        if "Note" in data:
            print(f"API Limit Reached: {data['Note']}")
            return None
            
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return None
            
        if data_key not in data:
            print(f"Unexpected data format: {data.keys()}")
            return None
            
        # Преобразуем данные в DataFrame
        df = pd.DataFrame.from_dict(data[data_key], orient='index')
        df = df.astype(float)
        close = df["4. close"]
        
        # Рассчитываем RSI
        period = get_rsi_period(user_id)
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        result = round(rsi.iloc[-1], 2)
        
        rsi_cache[cache_key] = (result, time.time())
        return result
        
    except Exception as e:
        print(f"Error calculating RSI for {symbol}: {str(e)}")
        return None