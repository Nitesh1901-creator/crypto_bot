"""Position sizing helpers."""

from __future__ import annotations

from typing import Literal


def compute_qty(
    qty_mode: Literal["fixed", "percent"],
    qty_value: float,
    mark_price: float,
    equity: float | None = None,
) -> float:
    if qty_mode == "fixed":
        return max(qty_value / max(mark_price, 1e-9), 0.0)
    if qty_mode == "percent":
        if equity is None:
            raise ValueError("equity required for percent sizing")
        return max((qty_value / 100.0) * equity / max(mark_price, 1e-9), 0.0)
    raise ValueError("qty_mode must be fixed|percent")
