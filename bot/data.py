import ccxt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

exchange = ccxt.oanda({
    'enableRateLimit': True,
    'apiKey': 'YOUR_OANDA_API_KEY',  # Замените, если требуется авторизация
})

def fetch_ohlcv(symbol='EUR/USD', timeframe='1h', limit=100):
    try:
        # OANDA использует символы с префиксом, например EUR/USD
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except Exception as e:
        logger.error(f"Ошибка получения данных для {symbol}: {e}")
        return None
