"""Exchange adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ExchangeAdapter(ABC):
    @abstractmethod
    def get_server_time(self) -> int:
        ...

    @abstractmethod
    def get_exchange_info(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def get_mark_price(self, symbol: str) -> float:
        ...

    @abstractmethod
    def get_best_bid_ask(self, symbol: str) -> Dict[str, float]:
        ...

    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str,
        price: Optional[float] = None,
        reduce_only: bool = False,
        position_side: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> None:
        ...

    @abstractmethod
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int) -> None:
        ...

    @abstractmethod
    def set_margin_type(self, symbol: str, margin_type: str) -> None:
        ...

    @abstractmethod
    def set_position_mode(self, hedge_mode: bool) -> None:
        ...

    @abstractmethod
    def get_account_balance(self) -> Dict[str, Any]:
        ...

