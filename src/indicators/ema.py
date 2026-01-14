"""EMA indicator."""

from __future__ import annotations

from typing import List


def ema(prices: List[float], period: int) -> List[float]:
    if period <= 0:
        raise ValueError("EMA period must be positive")
    if not prices:
        return []
    k = 2 / (period + 1)
    out: List[float] = []
    prev = prices[0]
    out.append(prev)
    for price in prices[1:]:
        prev = price * k + prev * (1 - k)
        out.append(prev)
    return out

