"""SuperTrend indicator."""

from __future__ import annotations

from typing import List, Tuple

from .atr import atr


def supertrend(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int,
    multiplier: float,
) -> Tuple[List[float], List[int]]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("High, low, close lengths must match")
    atr_vals = atr(highs, lows, closes, period)
    upper: List[float] = []
    lower: List[float] = []
    for h, l, a in zip(highs, lows, atr_vals):
        mid = (h + l) / 2
        upper.append(mid + multiplier * a)
        lower.append(mid - multiplier * a)

    st_vals: List[float] = []
    dirs: List[int] = []
    for i in range(len(closes)):
        if i == 0:
            st_vals.append(upper[i])
            dirs.append(1)
            continue
        prev_st = st_vals[-1]
        prev_dir = dirs[-1]
        close = closes[i]
        if close > upper[i - 1]:
            direction = 1
        elif close < lower[i - 1]:
            direction = -1
        else:
            direction = prev_dir

        if direction == 1:
            st_val = max(lower[i], prev_st)
        else:
            st_val = min(upper[i], prev_st)
        st_vals.append(st_val)
        dirs.append(direction)
    return st_vals, dirs

