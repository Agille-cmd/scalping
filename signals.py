from typing import Literal, Optional
import pandas as pd
from data import fetch_candle_data
from indicators import *
from config import ACTIVE_TRADING_HOURS
from datetime import datetime

SignalType = Literal["CALL", "PUT", None]

def check_signal(symbol: str) -> Optional[dict]:
    """Анализирует график и возвращает сигнал."""
    data = fetch_candle_data(symbol)
    if data is None or len(data) < 50:
        return None

    # Расчёт индикаторов
    data["rsi"] = calculate_rsi(data, 7)
    data["ema20"] = calculate_ema(data, 20)
    data["ema50"] = calculate_ema(data, 50)
    data["bb_upper"], data["bb_lower"] = calculate_bollinger_bands(data)
    
    last_candle = data.iloc[-1]
    prev_candle = data.iloc[-2]
    current_hour = datetime.utcnow().hour

    # Проверка активных часов
    is_active_time = any(start <= current_hour < end for start, end in ACTIVE_TRADING_HOURS)
    if not is_active_time:
        return None

    # Условия для CALL (покупка)
    call_conditions = (
        last_candle["close"] <= last_candle["bb_lower"] and
        last_candle["rsi"] < 20 and
        (last_candle["close"] > last_candle["ema50"] or data["ema20"].iloc[-1] > data["ema50"].iloc[-1]) and
        is_bullish_candle(last_candle, prev_candle)
    )

    # Условия для PUT (продажа)
    put_conditions = (
        last_candle["close"] >= last_candle["bb_upper"] and
        last_candle["rsi"] > 80 and
        (last_candle["close"] < last_candle["ema50"] or data["ema20"].iloc[-1] < data["ema50"].iloc[-1]) and
        is_bearish_candle(last_candle, prev_candle)
    )

    if call_conditions:
        return {"signal": "CALL", "confidence": calculate_confidence(data, "CALL")}
    elif put_conditions:
        return {"signal": "PUT", "confidence": calculate_confidence(data, "PUT")}
    return None

def calculate_confidence(data: pd.DataFrame, signal_type: SignalType) -> int:
    """Оценка уверенности сигнала (0-100%)."""
    last_candle = data.iloc[-1]
    rsi = last_candle["rsi"]
    bb_width = (data["bb_upper"].iloc[-1] - data["bb_lower"].iloc[-1]) / last_candle["close"]

    confidence = 60  # Базовая уверенность

    # Корректировка на основе RSI
    if signal_type == "CALL" and rsi < 15:
        confidence += 15
    elif signal_type == "PUT" and rsi > 85:
        confidence += 15

    # Корректировка на волатильность
    if bb_width > 0.005:
        confidence += 10

    return min(confidence, 90)  # Не более 90%