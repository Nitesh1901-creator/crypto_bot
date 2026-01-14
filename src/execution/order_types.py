"""Order type helpers and enums."""

from __future__ import annotations

from enum import Enum


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

