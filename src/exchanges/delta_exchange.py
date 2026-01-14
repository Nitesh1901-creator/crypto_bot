"""Delta Exchange adapter scaffolding with mock fallback."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import ExchangeAdapter

LOGGER = logging.getLogger(__name__)


class DeltaExchangeAdapter(ExchangeAdapter):
    """Minimal Delta Exchange adapter scaffold."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.delta.exchange") -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def get_server_time(self) -> int:
        LOGGER.warning("Delta get_server_time not implemented; returning 0.")
        return 0

    def get_exchange_info(self) -> Dict[str, Any]:
        LOGGER.warning("Delta get_exchange_info not implemented; returning empty.")
        return {}

    def get_mark_price(self, symbol: str) -> float:
        LOGGER.warning("Delta get_mark_price not implemented; returning 0.")
        return 0.0

    def get_best_bid_ask(self, symbol: str) -> Dict[str, float]:
        LOGGER.warning("Delta get_best_bid_ask not implemented; returning 0/0.")
        return {"bid": 0.0, "ask": 0.0}

    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        LOGGER.warning("Delta get_klines not implemented; returning empty.")
        return []

    def get_positions(self) -> List[Dict[str, Any]]:
        LOGGER.warning("Delta get_positions not implemented; returning empty.")
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
        LOGGER.warning("Delta place_order not implemented; returning mock.")
        return {"symbol": symbol, "side": side, "origQty": qty, "price": price or 0.0, "orderId": client_id or "mock"}

    def cancel_order(self, symbol: str, order_id: str) -> None:
        LOGGER.warning("Delta cancel_order not implemented.")
        return None

    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        LOGGER.warning("Delta get_open_orders not implemented; returning empty.")
        return []

    def set_leverage(self, symbol: str, leverage: int) -> None:
        LOGGER.warning("Delta set_leverage not implemented.")
        return None

    def set_margin_type(self, symbol: str, margin_type: str) -> None:
        LOGGER.warning("Delta set_margin_type not implemented.")
        return None

    def set_position_mode(self, hedge_mode: bool) -> None:
        LOGGER.warning("Delta set_position_mode not implemented.")
        return None

    def get_account_balance(self) -> Dict[str, Any]:
        LOGGER.warning("Delta get_account_balance not implemented; returning zero.")
        return {"balance": 0.0}
