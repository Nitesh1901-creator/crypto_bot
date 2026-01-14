"""Execution engine enforcing filters and writing trades/positions."""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional

from src.datastore.csv_store import CSVStore
from src.execution.order_types import OrderType, PositionSide
from src.pnl.calculator import bucket_daily
from src.utils.time import utc_now

LOGGER = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(
        self, trades_store: CSVStore, positions_store: CSVStore, pnl_store: CSVStore | None, fees_bps: float, slippage_bps: float
    ) -> None:
        self.trades_store = trades_store
        self.positions_store = positions_store
        self.pnl_store = pnl_store
        self.fees_bps = fees_bps
        self.slippage_bps = slippage_bps

    def _record_trade(
        self,
        exchange: str,
        symbol: str,
        side: str,
        position_side: str,
        qty: float,
        price: float,
        reason: str,
        order_id: str,
        client_id: Optional[str],
    ) -> Dict[str, str]:
        notional = price * qty
        fee = notional * (self.fees_bps / 10000)
        slippage = notional * (self.slippage_bps / 10000)
        trade = {
            "trade_id": str(uuid.uuid4()),
            "timestamp_utc": utc_now().isoformat(),
            "exchange": exchange,
            "symbol": symbol,
            "side": side,
            "position_side": position_side,
            "qty": str(qty),
            "price": str(price),
            "notional_usdt": str(notional),
            "fee": str(fee),
            "fee_asset": "USDT",
            "fee_usdt": str(fee),
            "order_id": order_id,
            "client_id": client_id or "",
            "reason": reason,
            "expected_price": "",
            "slippage_usdt": str(slippage),
        }
        self.trades_store.append(trade)
        return trade

    def enter_position(
        self,
        exchange: str,
        symbol: str,
        side: PositionSide,
        qty: float,
        price: float,
        strategy: str,
        trailing_mode: str,
        stop_loss: Optional[float] = None,
    ) -> Dict[str, str]:
        position_id = str(uuid.uuid4())
        now = utc_now().isoformat()
        entry_notional = price * qty
        trade = self._record_trade(
            exchange, symbol, "BUY" if side == PositionSide.LONG else "SELL", side.value, qty, price, "ENTER", "mock", None
        )
        fees_usdt = float(trade["fee_usdt"])
        slippage_usdt = float(trade["slippage_usdt"])
        self.positions_store.append(
            {
                "position_id": position_id,
                "symbol": symbol,
                "side": side.value,
                "qty": str(qty),
                "entry_time_utc": now,
                "entry_price": str(price),
                "exit_time_utc": "",
                "exit_price": "",
                "status": "OPEN",
                "strategy": strategy,
                "stop_loss": "" if stop_loss is None else str(stop_loss),
                "trailing_stop": "",
                "trailing_mode": trailing_mode,
                "total_fees_usdt": str(fees_usdt),
                "total_slippage_usdt": str(slippage_usdt),
                "realized_gross_pnl_usdt": "",
                "realized_net_pnl_usdt": "",
                "entry_notional_usdt": str(entry_notional),
                "exit_notional_usdt": "",
                "avg_notional_usdt": "",
                "gross_return_pct": "",
                "net_return_pct": "",
                "exit_reason": "",
                "last_update_utc": now,
            }
        )
        return {"position_id": position_id, "trade": trade}

    def exit_position(
        self,
        exchange: str,
        position: Dict[str, str],
        price: float,
        reason: str,
    ) -> Dict[str, str]:
        side = PositionSide.SHORT if position["side"].upper() == "LONG" else PositionSide.LONG
        qty = float(position["qty"])
        trade = self._record_trade(
            exchange,
            position["symbol"],
            "BUY" if side == PositionSide.LONG else "SELL",
            side.value,
            qty,
            price,
            "EXIT",
            "mock",
            None,
        )
        # update position row
        rows = self.positions_store.read_all()
        for row in rows:
            if row["position_id"] == position["position_id"]:
                entry_price = float(row["entry_price"])
                entry_notional = float(row["entry_notional_usdt"])
                total_fees = float(row.get("total_fees_usdt") or 0) + float(trade["fee_usdt"])
                total_slippage = float(row.get("total_slippage_usdt") or 0) + float(trade["slippage_usdt"])
                gross = (price - entry_price) * qty if position["side"].upper() == "LONG" else (entry_price - price) * qty
                net = gross - total_fees - total_slippage
                gross_return_pct = (gross / entry_notional) * 100 if entry_notional else 0.0
                net_return_pct = (net / entry_notional) * 100 if entry_notional else 0.0
                row["status"] = "CLOSED"
                row["exit_price"] = str(price)
                row["exit_time_utc"] = utc_now().isoformat()
                row["exit_notional_usdt"] = str(price * qty)
                row["avg_notional_usdt"] = str((float(row["entry_notional_usdt"]) + price * qty) / 2)
                row["exit_reason"] = reason
                row["last_update_utc"] = utc_now().isoformat()
                row["total_fees_usdt"] = str(total_fees)
                row["total_slippage_usdt"] = str(total_slippage)
                row["realized_gross_pnl_usdt"] = str(gross)
                row["realized_net_pnl_usdt"] = str(net)
                row["gross_return_pct"] = str(gross_return_pct)
                row["net_return_pct"] = str(net_return_pct)
                break
        self.positions_store.write_all(rows)
        # Update daily PnL bucket for closed positions
        if self.pnl_store:
            closed_positions = [r for r in rows if r.get("status") == "CLOSED"]
            bucket_daily(self.pnl_store, closed_positions)
        return {"trade": trade, "position": position}
