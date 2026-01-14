"""Strategy interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.market_data.engine import SymbolState


class Signal(ABC):
    ...


class Strategy(ABC):
    name: str

    @abstractmethod
    def evaluate(self, state: SymbolState) -> Optional[Dict[str, str]]:
        """Return a signal dict or None."""
        ...

