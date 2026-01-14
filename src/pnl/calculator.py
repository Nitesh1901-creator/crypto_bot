"""PnL calculations and daily bucketing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from src.datastore.csv_store import CSVStore


def _gross(side: str, entry: float, exit: float, qty: float) -> float:
    if side.upper() == "LONG":
        return (exit - entry) * qty
    if side.upper() == "SHORT":
        return (entry - exit) * qty
    raise ValueError("side must be LONG|SHORT")


@dataclass
class PositionPnL:
    gross: float
    fees: float
    slippage: float
    net: float
    entry_notional: float
    exit_notional: float


def compute_position_pnl(position: Dict[str, str]) -> PositionPnL:
    entry_price = float(position["entry_price"])
    exit_price = float(position.get("exit_price") or entry_price)
    qty = float(position["qty"])
    side = position["side"]
    fees = float(position.get("total_fees_usdt") or 0)
    slippage = float(position.get("total_slippage_usdt") or 0)
    gross = _gross(side, entry_price, exit_price, qty)
    entry_notional = entry_price * qty
    exit_notional = exit_price * qty
    net = gross - fees - slippage
    return PositionPnL(
        gross=gross,
        fees=fees,
        slippage=slippage,
        net=net,
        entry_notional=entry_notional,
        exit_notional=exit_notional,
    )


def bucket_daily(pnl_store: CSVStore, closed_positions: List[Dict[str, str]]) -> None:
    rows = pnl_store.read_all()
    index = {r["date_utc"]: r for r in rows}
    wins: Dict[str, List[float]] = {}
    losses: Dict[str, List[float]] = {}
    for pos in closed_positions:
        if pos.get("exit_time_utc") == "":
            continue
        exit_dt = datetime.fromisoformat(pos["exit_time_utc"]).astimezone(timezone.utc)
        key = exit_dt.date().isoformat()
        pnl = compute_position_pnl(pos)
        rec = index.get(
            key,
            {
                "date_utc": key,
                "gross_pnl_usdt": "0",
                "net_pnl_usdt": "0",
                "fees_usdt": "0",
                "slippage_usdt": "0",
                "traded_notional_usdt": "0",
                "exit_notional_usdt": "0",
                "trade_count": "0",
                "win_count": "0",
                "loss_count": "0",
                "avg_win_usdt": "0",
                "avg_loss_usdt": "0",
                "profit_factor": "0",
                "win_rate": "0",
                "updated_at_utc": "",
            },
        )
        rec["gross_pnl_usdt"] = str(float(rec["gross_pnl_usdt"]) + pnl.gross)
        rec["net_pnl_usdt"] = str(float(rec["net_pnl_usdt"]) + pnl.net)
        rec["fees_usdt"] = str(float(rec["fees_usdt"]) + pnl.fees)
        rec["slippage_usdt"] = str(float(rec["slippage_usdt"]) + pnl.slippage)
        rec["traded_notional_usdt"] = str(float(rec["traded_notional_usdt"]) + pnl.entry_notional)
        rec["exit_notional_usdt"] = str(float(rec["exit_notional_usdt"]) + pnl.exit_notional)
        rec["trade_count"] = str(int(rec["trade_count"]) + 1)
        if pnl.net >= 0:
            rec["win_count"] = str(int(rec["win_count"]) + 1)
            wins.setdefault(key, []).append(pnl.net)
        else:
            rec["loss_count"] = str(int(rec["loss_count"]) + 1)
            losses.setdefault(key, []).append(abs(pnl.net))
        rec["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        index[key] = rec
    # Post-process averages and profit factor
    for key, rec in index.items():
        win_list = wins.get(key, [])
        loss_list = losses.get(key, [])
        avg_win = sum(win_list) / len(win_list) if win_list else 0.0
        avg_loss = sum(loss_list) / len(loss_list) if loss_list else 0.0
        profit_factor = (sum(win_list) / sum(loss_list)) if loss_list else (float("inf") if win_list else 0.0)
        trade_count = int(rec["trade_count"]) or 1
        win_rate = (int(rec["win_count"]) / trade_count) * 100
        rec["avg_win_usdt"] = str(avg_win)
        rec["avg_loss_usdt"] = str(avg_loss)
        rec["profit_factor"] = "inf" if profit_factor == float("inf") else str(profit_factor)
        rec["win_rate"] = str(win_rate)
    pnl_store.write_all(list(index.values()))
