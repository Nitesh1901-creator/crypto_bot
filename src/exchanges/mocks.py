"""Mock adapters for paper/testing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import ExchangeAdapter


class MockDeltaAdapter(ExchangeAdapter):
    def get_server_time(self) -> int:
        return 0

    def get_exchange_info(self) -> Dict[str, Any]:
        return {}

    def get_mark_price(self, symbol: str) -> float:
        return 0.0

    def get_best_bid_ask(self, symbol: str) -> Dict[str, float]:
        return {"bid": 0.0, "ask": 0.0}

    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        return []

    def get_positions(self) -> List[Dict[str, Any]]:
        return []

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
        return {"symbol": symbol, "side": side, "origQty": qty, "price": price or 0.0, "orderId": client_id or "mock"}

    def cancel_order(self, symbol: str, order_id: str) -> None:
        return None

    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        return []

    def set_leverage(self, symbol: str, leverage: int) -> None:
        return None

    def set_margin_type(self, symbol: str, margin_type: str) -> None:
        return None

    def set_position_mode(self, hedge_mode: bool) -> None:
        return None

    def get_account_balance(self) -> Dict[str, Any]:
        return {"balance": 0.0}

