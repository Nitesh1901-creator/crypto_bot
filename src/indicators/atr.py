"""ATR indicator."""

from __future__ import annotations

from typing import List


def atr(highs: List[float], lows: List[float], closes: List[float], period: int) -> List[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("High, low, close lengths must match")
    if period <= 0:
        raise ValueError("ATR period must be positive")
    trs: List[float] = []
    for i in range(len(highs)):
        if i == 0:
            tr = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        trs.append(tr)
    if len(trs) < period:
        return []
    out: List[float] = [0.0] * len(trs)
    prev = sum(trs[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(trs)):
        prev = (prev * (period - 1) + trs[i]) / period
        out[i] = prev
    for i in range(period - 1):
        out[i] = out[period - 1]
    return out

