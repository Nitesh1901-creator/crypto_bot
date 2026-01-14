"""Strategy router handling priority and exits."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.market_data.engine import SymbolState
from src.strategy.st_line_ema_strategy import STLineEMAStrategy
from src.strategy.breakout_retest_strategy import BreakoutRetestStrategy

LOGGER = logging.getLogger(__name__)


class StrategyRouter:
    def __init__(self) -> None:
        # Strategy A holds cross state; Strategy B is stateless aside from SymbolState fields.
        self.st_strategy = STLineEMAStrategy()

    def evaluate(self, state: SymbolState, entry: object) -> Optional[Dict[str, str]]:
        # Priority: Strategy B > Strategy A
        if getattr(entry, "use_strategy_b", False):
            strat_b = BreakoutRetestStrategy(
                window=getattr(entry, "range_window", 120),
                max_width_pct=getattr(entry, "max_range_width_pct", 0.006),
                retest_max_bars=getattr(entry, "retest_max_bars", 30),
            )
            sig_b = strat_b.evaluate(state)
            if sig_b:
                LOGGER.debug("Strategy Breakout_Retest hit %s: %s", state.symbol, sig_b)
                return sig_b
            LOGGER.debug("Strategy Breakout_Retest no signal for %s", state.symbol)

        if getattr(entry, "use_strategy_a", False):
            sig_a = self.st_strategy.evaluate(state)
            if sig_a:
                LOGGER.debug("Strategy ST_EMA50_Cross hit %s: %s", state.symbol, sig_a)
                return sig_a
            LOGGER.debug("Strategy ST_EMA50_Cross no signal for %s", state.symbol)
        return None
