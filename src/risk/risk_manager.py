"""Risk management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from src.config.loader import RiskConfig


@dataclass
class LossRecord:
    timestamp: datetime
    amount: float


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self.daily_loss: float = 0.0
        self.last_loss: Optional[LossRecord] = None

    def record_loss(self, amount: float, ts: datetime) -> None:
        self.daily_loss += max(amount, 0.0)
        self.last_loss = LossRecord(timestamp=ts, amount=amount)

    def allow_new_position(self, open_positions: int, equity: float) -> bool:
        if open_positions >= self.config.max_open_positions:
            return False
        if self.daily_loss >= self.config.max_daily_loss_usdt:
            return False
        if equity * self.config.max_leverage <= 0:
            return False
        return True

