"""Binance USDT-M Futures adapter (skeleton)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ExchangeAdapter

LOGGER = logging.getLogger(__name__)

REST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class BinanceFuturesAdapter(ExchangeAdapter):
    """Binance USDT-M Futures adapter (REST skeleton)."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=REST_TIMEOUT)
        return self.session

    def _headers(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        async with session.get(url, headers=self._headers(), params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    # Public endpoints
    async def get_server_time(self) -> int:
        data = await self._get("/fapi/v1/time")
        return int(data.get("serverTime", 0))

    async def get_exchange_info(self) -> Dict[str, Any]:
        return await self._get("/fapi/v1/exchangeInfo")

    async def get_mark_price(self, symbol: str) -> float:
        data = await self._get("/fapi/v1/premiumIndex", params={"symbol": symbol})
        return float(data.get("markPrice", 0))

    async def get_best_bid_ask(self, symbol: str) -> Dict[str, float]:
        data = await self._get("/fapi/v1/ticker/bookTicker", params={"symbol": symbol})
        return {"bid": float(data.get("bidPrice", 0)), "ask": float(data.get("askPrice", 0))}

    async def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        data = await self._get("/fapi/v1/klines", params={"symbol": symbol, "interval": interval, "limit": limit})
        # Each kline: [ openTime, open, high, low, close, volume, closeTime, ... ]
        klines: List[Dict[str, Any]] = []
        for row in data:
            klines.append(
                {
                    "open_time": int(row[0]),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                    "close_time": int(row[6]),
                }
            )
        return klines

    # Authenticated stubs (signing omitted in scaffold)
    async def get_positions(self) -> List[Dict[str, Any]]:
        LOGGER.warning("get_positions not implemented; returning empty list.")
        return []

    async def place_order(
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
        LOGGER.info("MOCK place_order %s %s qty=%s", symbol, side, qty)
        return {"symbol": symbol, "side": side, "origQty": qty, "price": price or 0.0, "orderId": client_id or "mock"}

    async def cancel_order(self, symbol: str, order_id: str) -> None:
        LOGGER.info("MOCK cancel_order %s %s", symbol, order_id)

    async def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        return []

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        LOGGER.info("MOCK set_leverage %s %s", symbol, leverage)

    async def set_margin_type(self, symbol: str, margin_type: str) -> None:
        LOGGER.info("MOCK set_margin_type %s %s", symbol, margin_type)

    async def set_position_mode(self, hedge_mode: bool) -> None:
        LOGGER.info("MOCK set_position_mode hedge=%s", hedge_mode)

    async def get_account_balance(self) -> Dict[str, Any]:
        return {"balance": 0.0}
