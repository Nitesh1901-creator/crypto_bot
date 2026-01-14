"""Range detection for breakout/retest strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RangeInfo:
    range_high: float
    range_low: float
    valid: bool


def detect_range(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    atr_now: float,
    window: int,
    max_width_pct: float,
) -> RangeInfo:
    if len(highs) < window:
        return RangeInfo(0, 0, False)
    subset_highs = highs[-window:]
    subset_lows = lows[-window:]
    subset_closes = closes[-window:]
    r_high = max(subset_highs)
    r_low = min(subset_lows)
    mid = (r_high + r_low) / 2 or 1e-9
    width_pct = (r_high - r_low) / mid
    return RangeInfo(r_high, r_low, width_pct <= max_width_pct)

