import ccxt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'
    }
})

def fetch_ohlcv(symbol='BTC/USDT', timeframe='1h', limit=100):
    try:
        symbol = symbol.replace('/', '')
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except Exception as e:
        logger.error(f"Ошибка получения данных для {symbol}: {e}")
        return None