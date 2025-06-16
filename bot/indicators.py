import requests
import pandas as pd
from bot.data import ALPHA_VANTAGE_API_KEY
from bot.user_data import get_rsi_period
import time

rsi_cache = {}
CACHE_TIME = 60  # 1 минута

def get_rsi(user_id, symbol):
    cache_key = (user_id, symbol)
    if cache_key in rsi_cache:
        value, timestamp = rsi_cache[cache_key]
        if time.time() - timestamp < CACHE_TIME:
            return value
    
    try:
        from_symbol, to_symbol = symbol.split('/')
        url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        data = requests.get(url).json()
        
        df = pd.DataFrame(data["Time Series FX (Daily)"]).T.astype(float)
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
        print(f"Ошибка RSI для {symbol}: {e}")
        return None