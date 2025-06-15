from ta.momentum import RSIIndicator
import logging

logger = logging.getLogger(__name__)

def calculate_rsi(df, period=14):
    try:
        if df is None or df.empty:
            return None
            
        rsi = RSIIndicator(close=df['close'], window=period)
        return rsi.rsi().iloc[-1]
    except Exception as e:
        logger.error(f"Ошибка расчета RSI: {e}")
        return None