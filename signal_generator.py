import ccxt
from typing import List, Dict, Optional

# Utility functions

def sma(values: List[float], length: int) -> Optional[float]:
    if len(values) < length:
        return None
    return sum(values[-length:]) / length


def atr(highs: List[float], lows: List[float], closes: List[float], length: int = 14) -> Optional[float]:
    if len(closes) < length + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    if len(trs) < length:
        return None
    return sum(trs[-length:]) / length


def temperature_indicator(closes: List[float], length: int) -> Optional[float]:
    ma = sma(closes, length)
    if ma is None:
        return None
    return 100 * (closes[-1] - ma) / ma


def generate_signal(ohlcv: List[List[float]], temp_len: int = 20, long_th: float = 0.5, short_th: float = 0.5) -> Optional[Dict[str, object]]:
    highs = [c[2] for c in ohlcv]
    lows = [c[3] for c in ohlcv]
    closes = [c[4] for c in ohlcv]

    temp = temperature_indicator(closes, temp_len)
    if temp is None:
        return None

    long_entry = temp > long_th
    short_entry = temp < -short_th
    if not (long_entry or short_entry):
        return None

    last_close = closes[-1]
    avg_tr = atr(highs, lows, closes)
    if avg_tr is None:
        return None

    if long_entry:
        stop_loss = last_close - avg_tr
        tps = [last_close + avg_tr * (i + 1) for i in range(3)]
        side = 'LONG'
    else:
        stop_loss = last_close + avg_tr
        tps = [last_close - avg_tr * (i + 1) for i in range(3)]
        side = 'SHORT'

    probabilities = [0.6, 0.4, 0.2]

    return {
        'side': side,
        'entry': last_close,
        'stop_loss': stop_loss,
        'take_profits': tps,
        'probabilities': probabilities,
    }


def analyze_markets(timeframe: str = '1h', limit: int = 100) -> Dict[str, Dict[str, object]]:
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    symbols = [s for s in markets if s.endswith('/USDT')]

    signals: Dict[str, Dict[str, object]] = {}
    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception:
            continue
        sig = generate_signal(ohlcv)
        if sig:
            sig['timeframe'] = timeframe
            signals[symbol] = sig
    return signals


if __name__ == '__main__':
    # Example usage
    results = analyze_markets()
    for pair, signal in results.items():
        print(f"{pair}: {signal}")
