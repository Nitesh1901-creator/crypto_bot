"""Market data engine maintaining per-symbol state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
from collections import deque

from src.indicators.ema import ema
from src.indicators.atr import atr
from src.indicators.supertrend import supertrend


@dataclass
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


@dataclass
class SymbolState:
    symbol: str
    candles: Deque[Candle] = field(default_factory=lambda: deque(maxlen=1500))
    ema50: Optional[float] = None
    prev_ema: Optional[float] = None
    atr_val: Optional[float] = None
    st_dir: Optional[int] = None
    st_val: Optional[float] = None
    prev_st_dir: Optional[int] = None
    prev_st_val: Optional[float] = None
    last_close_time: Optional[int] = None
    b_state: Optional[str] = None
    b_level: Optional[float] = None
    b_started_at: Optional[int] = None
    ema_period: int = 50
    atr_period: int = 10
    st_period: int = 10
    st_multiplier: float = 3.0


class MarketDataEngine:
    """Keeps latest closed candles and indicators per symbol."""

    def __init__(self, lookback: int = 1200) -> None:
        self.lookback = lookback
        self.symbols: Dict[str, SymbolState] = {}

    def ensure_symbol(self, symbol: str) -> SymbolState:
        if symbol not in self.symbols:
            self.symbols[symbol] = SymbolState(symbol=symbol, candles=deque(maxlen=self.lookback + 300))
        return self.symbols[symbol]

    def update_candles(self, symbol: str, closed_candles: List[Candle], params: object | None = None) -> None:
        state = self.ensure_symbol(symbol)
        if params is not None:
            state.ema_period = getattr(params, "ema_period", state.ema_period)
            state.atr_period = getattr(params, "supertrend_period", state.atr_period)
            state.st_period = getattr(params, "supertrend_period", state.st_period)
            state.st_multiplier = getattr(params, "supertrend_multiplier", state.st_multiplier)
        for c in closed_candles:
            if state.last_close_time is not None and c.close_time <= state.last_close_time:
                continue
            state.candles.append(c)
            state.last_close_time = c.close_time
        if len(state.candles) >= state.ema_period:
            closes = [c.close for c in state.candles]
            highs = [c.high for c in state.candles]
            lows = [c.low for c in state.candles]
            ema_series = ema(closes, state.ema_period)
            state.prev_ema = state.ema50
            state.ema50 = ema_series[-1]
            state.atr_val = atr(highs, lows, closes, state.atr_period)[-1]
            st_vals, st_dirs = supertrend(highs, lows, closes, state.st_period, state.st_multiplier)
            state.prev_st_val = state.st_val
            state.prev_st_dir = state.st_dir
            state.st_val = st_vals[-1]
            state.st_dir = st_dirs[-1]
