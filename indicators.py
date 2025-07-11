import pandas as pd
import ta

def calculate_rsi(data: pd.DataFrame, period: int = 7) -> pd.Series:
    """Расчёт RSI с помощью библиотеки ta."""
    return ta.momentum.RSIIndicator(data["close"], window=period).rsi()

def calculate_ema(data: pd.DataFrame, window: int) -> pd.Series:
    """Расчёт EMA."""
    return ta.trend.EMAIndicator(data["close"], window=window).ema_indicator()

def calculate_bollinger_bands(data: pd.DataFrame, window: int = 20, dev: int = 2) -> tuple[pd.Series, pd.Series]:
    """Расчёт Bollinger Bands."""
    bb = ta.volatility.BollingerBands(data["close"], window=window, window_dev=dev)
    return bb.bollinger_hband(), bb.bollinger_lband()

def is_bullish_candle(candle: pd.Series, prev_candle: pd.Series) -> bool:
    """Определяет, является ли свеча бычьим паттерном."""
    body = abs(candle["open"] - candle["close"])
    lower_shadow = (candle["close"] - candle["low"]) > (candle["high"] - candle["close"])
    is_doji = body <= 0.0002 * candle["close"]  # Доджи (очень маленькое тело)
    is_engulfing = (candle["close"] > prev_candle["open"]) and (candle["open"] < prev_candle["close"])
    return lower_shadow or is_doji or is_engulfing

def is_bearish_candle(candle: pd.Series, prev_candle: pd.Series) -> bool:
    """Определяет, является ли свеча медвежьим паттерном."""
    body = abs(candle["open"] - candle["close"])
    upper_shadow = (candle["high"] - candle["close"]) > (candle["close"] - candle["low"])
    is_doji = body <= 0.0002 * candle["close"]
    is_engulfing = (candle["close"] < prev_candle["open"]) and (candle["open"] > prev_candle["close"])
    return upper_shadow or is_doji or is_engulfing