"""Strategy B: Range breakout + retest skeleton."""

from __future__ import annotations

from typing import Dict, Optional

from src.levels.range_detector import detect_range
from src.market_data.engine import SymbolState

STATE_IDLE = "IDLE"
STATE_WAIT_RETEST_LONG = "WAIT_RETEST_LONG"
STATE_WAIT_RETEST_SHORT = "WAIT_RETEST_SHORT"


class BreakoutRetestStrategy:
    """Strategy B: breakout/breakdown then retest."""

    name = "Breakout_Retest"

    def __init__(self, window: int = 120, max_width_pct: float = 0.006, retest_max_bars: int = 30) -> None:
        self.window = window
        self.max_width_pct = max_width_pct
        self.retest_max_bars = retest_max_bars

    def evaluate(self, state: SymbolState) -> Optional[Dict[str, str]]:
        if len(state.candles) < self.window or state.atr_val is None or state.ema50 is None or state.st_dir is None:
            return None
        highs = [c.high for c in state.candles]
        lows = [c.low for c in state.candles]
        closes = [c.close for c in state.candles]
        rng = detect_range(highs, lows, closes, state.atr_val, self.window, self.max_width_pct)
        curr = state.candles[-1]
        tol = 0.05 * state.atr_val

        if getattr(state, "b_state", None) is None:
            state.b_state = STATE_IDLE
            state.b_level = None
            state.b_started_at = 0

        # Breakout detection
        if state.b_state == STATE_IDLE and rng.valid:
            if curr.close > rng.range_high + tol and state.st_dir == 1 and curr.close > state.ema50:
                state.b_state = STATE_WAIT_RETEST_LONG
                state.b_level = rng.range_high
                state.b_started_at = len(state.candles)
            elif curr.close < rng.range_low - tol and state.st_dir == -1 and curr.close < state.ema50:
                state.b_state = STATE_WAIT_RETEST_SHORT
                state.b_level = rng.range_low
                state.b_started_at = len(state.candles)

        # Retest window exceeded
        if state.b_state in {STATE_WAIT_RETEST_LONG, STATE_WAIT_RETEST_SHORT}:
            if len(state.candles) - state.b_started_at > self.retest_max_bars:
                state.b_state = STATE_IDLE
                state.b_level = None

        signal: Optional[Dict[str, str]] = None
        if state.b_state == STATE_WAIT_RETEST_LONG and state.b_level is not None:
            if curr.low <= state.b_level + 0.25 * state.atr_val and curr.close >= state.b_level + 0.05 * state.atr_val:
                if curr.close > state.ema50 and state.st_dir == 1:
                    signal = {"action": "ENTER_LONG", "strategy": self.name}
                    state.b_state = STATE_IDLE
                    state.b_level = None
            elif state.st_dir == -1 or curr.close < state.ema50 or curr.close < state.b_level - 0.30 * state.atr_val:
                state.b_state = STATE_IDLE
                state.b_level = None

        if state.b_state == STATE_WAIT_RETEST_SHORT and state.b_level is not None:
            if curr.high >= state.b_level - 0.25 * state.atr_val and curr.close <= state.b_level - 0.05 * state.atr_val:
                if curr.close < state.ema50 and state.st_dir == -1:
                    signal = {"action": "ENTER_SHORT", "strategy": self.name}
                    state.b_state = STATE_IDLE
                    state.b_level = None
            elif state.st_dir == 1 or curr.close > state.ema50 or curr.close > state.b_level + 0.30 * state.atr_val:
                state.b_state = STATE_IDLE
                state.b_level = None

        return signal
