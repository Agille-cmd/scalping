import requests
import pandas as pd
from config import TWELVEDATA_API_KEYS
from datetime import datetime, timedelta

def fetch_candle_data(symbol: str, interval: str = "1min", limit: int = 100) -> pd.DataFrame | None:
    """Получает свечные данные с TwelveData API."""
    for api_key in TWELVEDATA_API_KEYS:
        try:
            url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={limit}&apikey={api_key.strip()}"
            response = requests.get(url, timeout=10).json()
            
            if "values" not in response:
                continue
                
            df = pd.DataFrame(response["values"])
            df = df.iloc[::-1].reset_index(drop=True)  # Переворачиваем DataFrame
            
            # Конвертация данных
            df["datetime"] = pd.to_datetime(df["datetime"])
            numeric_cols = ["open", "high", "low", "close"]
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            return df
            
        except Exception as e:
            print(f"Ошибка при запросе {symbol}: {e}")
    
    return None  # Если все ключи не сработали