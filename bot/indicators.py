# indicators.py — полная замена, без API, только TradingView WebSocket
from tradingview_ws import TradingView
from bot.data import AVAILABLE_PAIRS
from bot.user_data import get_rsi_period, get_time_interval

interval_map = {
    "1min": "1",
    "5min": "5",
    "15min": "15",
    "30min": "30",
    "1h": "60",
    "4h": "240",
    "1day": "1D",
}

def get_rsi(user_id, symbol):
    try:
        if symbol not in AVAILABLE_PAIRS:
            raise ValueError(f"Неверная валютная пара: {symbol}")

        base, quote = symbol.split("/")
        tv_symbol = f"{base}{quote}"

        interval_str = get_time_interval(user_id)
        interval = interval_map.get(interval_str)
        period = get_rsi_period(user_id)

        if not interval:
            raise ValueError(f"Неверный интервал: {interval_str}")

        tv = TradingView()
        indicator = {
            "study_type": "RSI",
            "inputs": {
                "length": period
            }
        }

        result = tv.get_indicator(
            symbol=tv_symbol,
            screener="forex",
            exchange="FX",
            interval=interval,
            indicator=indicator
        )

        if not result or not isinstance(result, dict):
            raise ValueError("Не удалось получить RSI из TradingView")

        rsi = result.get("value") or result.get(f"RSI")
        if rsi is None:
            raise ValueError("Пустой RSI")

        return round(float(rsi), 2)

    except Exception as e:
        print(f"⚠️ Ошибка в get_rsi через TradingView WS: {e}")
        return None
