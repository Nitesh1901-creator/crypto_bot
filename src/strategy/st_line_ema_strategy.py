"""Strategy A: SuperTrend line crossing EMA50."""

from __future__ import annotations

from typing import Dict, Optional

from src.market_data.engine import SymbolState


class STLineEMAStrategy:
    """Strategy A: SuperTrend line crosses EMA50; exit on flip or ST stop hit."""

    name = "ST_EMA50_Cross"

    def evaluate(self, state: SymbolState) -> Optional[Dict[str, str]]:
        if len(state.candles) < 2 or state.st_dir is None or state.ema50 is None or state.st_val is None:
            return None

        closes = [c.close for c in state.candles]
        highs = [c.high for c in state.candles]
        lows = [c.low for c in state.candles]
        curr_close = closes[-1]

        # Approximate prev values from penultimate candle snapshot.
        prev_close = closes[-2]
        prev_st_dir = state.prev_st_dir if state.prev_st_dir is not None else state.st_dir
        prev_st_val = state.prev_st_val if state.prev_st_val is not None else state.st_val
        prev_ema = state.prev_ema if state.prev_ema is not None else state.ema50
        prev_low = lows[-2]
        prev_high = highs[-2]

        signals: Dict[str, str] | None = None

        # Bullish cross: ST line moves from below EMA to above; price above EMA.
        if state.st_dir == 1 and prev_st_dir == -1 and prev_st_val <= prev_ema and state.st_val > state.ema50 and curr_close > state.ema50:
            signals = {"action": "ENTER_LONG", "strategy": self.name, "stop_loss": str(state.st_val)}

        # Bearish cross: ST line moves from above EMA to below; price below EMA.
        if state.st_dir == -1 and prev_st_dir == 1 and prev_st_val >= prev_ema and state.st_val < state.ema50 and curr_close < state.ema50:
            signals = {"action": "ENTER_SHORT", "strategy": self.name, "stop_loss": str(state.st_val)}

        # Update previous tracking on state for next evaluation.
        state.prev_st_dir = state.st_dir
        state.prev_st_val = state.st_val
        state.prev_ema = state.ema50
        return signals
