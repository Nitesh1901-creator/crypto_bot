"""Config loader."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict

import yaml


@dataclass
class PnLConfig:
    slippage_mode: str = "estimated"
    slippage_bps: float = 0.015


@dataclass
class RiskConfig:
    max_open_positions: int = 3
    max_daily_loss_usdt: float = 100.0
    max_leverage: int = 10
    cooldown_minutes_after_loss: int = 30
    min_order_notional_usdt: float = 5.5


@dataclass
class AppConfig:
    exchange: str = "binance"
    mode: str = "testnet"
    confirm_live: bool = False
    api_key: str | None = None
    api_secret: str | None = None
    hedge_mode: bool = True
    poll_interval_seconds: int = 1
    kline_refresh_seconds: int = 10
    universe_kline_lookback: int = 1200
    data_dir: str = "data"
    watchlist_path: str = "watchlist.csv"
    pnl: PnLConfig = field(default_factory=PnLConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)


def load_config(path: str | pathlib.Path) -> AppConfig:
    cfg_path = pathlib.Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    raw: Dict[str, Any] = yaml.safe_load(cfg_path.read_text()) or {}
    cfg = AppConfig(
        exchange=raw.get("exchange", "binance"),
        mode=raw.get("mode", "testnet"),
        confirm_live=bool(raw.get("confirm_live", False)),
        api_key=os.getenv("BINANCE_API_KEY") or raw.get("api_key"),
        api_secret=os.getenv("BINANCE_API_SECRET") or raw.get("api_secret"),
        hedge_mode=bool(raw.get("hedge_mode", True)),
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 1)),
        kline_refresh_seconds=int(raw.get("kline_refresh_seconds", 10)),
        universe_kline_lookback=int(raw.get("universe_kline_lookback", 1200)),
        data_dir=raw.get("data_dir", "data"),
        watchlist_path=raw.get("watchlist_path", "watchlist.csv"),
        pnl=PnLConfig(
            slippage_mode=raw.get("pnl", {}).get("slippage_mode", "estimated"),
            slippage_bps=float(raw.get("pnl", {}).get("slippage_bps", 0.015)),
        ),
        risk=RiskConfig(
            max_open_positions=int(raw.get("risk", {}).get("max_open_positions", 3)),
            max_daily_loss_usdt=float(raw.get("risk", {}).get("max_daily_loss_usdt", 100)),
            max_leverage=int(raw.get("risk", {}).get("max_leverage", 10)),
            cooldown_minutes_after_loss=int(raw.get("risk", {}).get("cooldown_minutes_after_loss", 30)),
            min_order_notional_usdt=float(raw.get("risk", {}).get("min_order_notional_usdt", 5.5)),
        ),
    )
    if cfg.mode.lower() == "live" and not cfg.confirm_live:
        raise ValueError("Refusing to run in live mode without confirm_live=true.")
    return cfg
