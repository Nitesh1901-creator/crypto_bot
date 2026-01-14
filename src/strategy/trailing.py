"""Trailing stop utilities supporting ATR, PCT, and SuperTrend modes."""

from __future__ import annotations

from typing import Dict, Tuple

from src.market_data.engine import Candle


def update_trailing_stop(
    side: str,
    mode: str,
    prev_trail: float | None,
    candle: Candle,
    entry_price: float,
    trail_params: Dict[str, float],
    atr_value: float | None,
    supertrend_value: float | None,
) -> Tuple[float, bool]:
    """
    Compute the next trailing stop and whether it was hit on this candle.

    Modes:
      - ATR: candidate = close - ATR*mult (LONG) / close + ATR*mult (SHORT)
      - PCT: candidate = close - entry*pct (LONG) / close + entry*pct (SHORT)
      - SUPERTREND: candidate = supertrend_value
    """
    side_upper = side.upper()
    mode_upper = mode.upper()
    if side_upper not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")

    if mode_upper == "ATR":
        if atr_value is None:
            raise ValueError("ATR value required for ATR trailing stop")
        mult = float(trail_params.get("atr_mult", 1.0))
        candidate = candle.close - atr_value * mult if side_upper == "LONG" else candle.close + atr_value * mult
    elif mode_upper == "PCT":
        pct = float(trail_params.get("pct", 0.0))
        offset = entry_price * pct
        candidate = candle.close - offset if side_upper == "LONG" else candle.close + offset
    elif mode_upper == "SUPERTREND":
        if supertrend_value is None:
            raise ValueError("SuperTrend value required for SUPERTREND trailing stop")
        candidate = supertrend_value
    else:
        raise ValueError(f"Unsupported trailing mode {mode}")

    if prev_trail is None:
        trail_stop = candidate
        hit = False
    else:
        if side_upper == "LONG":
            trail_stop = max(prev_trail, candidate)
            hit = candle.low <= trail_stop
        else:
            trail_stop = min(prev_trail, candidate)
            hit = candle.high >= trail_stop
    return trail_stop, hit

