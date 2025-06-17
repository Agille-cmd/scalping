import requests
import pandas as pd
from bot.data import ALPHA_VANTAGE_API_KEY
from bot.user_data import get_rsi_period, get_time_interval
import time

rsi_cache = {}
CACHE_TIME = 60  # 1 минута

def get_rsi(user_id, symbol):
    cache_key = (user_id, symbol, get_time_interval(user_id))
    if cache_key in rsi_cache:
        value, timestamp = rsi_cache[cache_key]
        if time.time() - timestamp < CACHE_TIME:
            return value
    
    try:
        from_symbol, to_symbol = symbol.split('/')
        interval = get_time_interval(user_id)
        
        # Для разных интервалов используем разные функции API
        if interval == "daily":
            url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            data_key = "Time Series FX (Daily)"
        else:
            url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_symbol}&to_symbol={to_symbol}&interval={interval}&apikey={ALPHA_VANTAGE_API_KEY}"
            data_key = f"Time Series FX ({interval})"
        
        response = requests.get(url)
        data = response.json()
        
        # Проверяем наличие ошибки в ответе
        if "Error Message" in data:
            print(f"API Error for {symbol}: {data['Error Message']}")
            return None
            
        if data_key not in data:
            print(f"Unexpected data format for {symbol}: {data.keys()}")
            return None
            
        df = pd.DataFrame(data[data_key]).T.astype(float)
        close = df["4. close"]
        period = get_rsi_period(user_id)
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        result = round(rsi.iloc[-1], 2)
        
        rsi_cache[cache_key] = (result, time.time())
        return result
        
    except Exception as e:
        print(f"Ошибка RSI для {symbol}: {str(e)}")
        return None