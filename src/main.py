"""CLI entrypoint for the crypto futures trading bot."""

from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.config.loader import AppConfig, load_config
from src.datastore.csv_store import CSVStore
from src.exchanges.binance_futures import BinanceFuturesAdapter
from src.exchanges.delta_exchange import DeltaExchangeAdapter
from src.exchanges.mocks import MockDeltaAdapter
from src.execution.engine import ExecutionEngine
from src.execution.order_types import PositionSide
from src.market_data.engine import MarketDataEngine, Candle, SymbolState
from src.risk.risk_manager import RiskManager
from src.risk.sizing import compute_qty
from src.strategy.router import StrategyRouter
from src.strategy.trailing import update_trailing_stop
from src.strategy.portfolio import Portfolio
from src.utils.logger import setup_logging
from src.utils.time import utc_now

LOGGER = logging.getLogger(__name__)


@dataclass
class WatchlistEntry:
    symbol: str
    enabled: bool
    leverage: int
    qty_mode: str
    qty_value: float
    ema_period: int
    supertrend_period: int
    supertrend_multiplier: float
    trailing_mode: str
    trailing_atr_mult: float
    trailing_pct: float
    use_strategy_a: bool
    use_strategy_b: bool
    breakout_mode: str
    range_window: int
    max_range_width_pct: float
    retest_max_bars: int


def load_watchlist(path: str | pathlib.Path) -> List[WatchlistEntry]:
    import csv

    entries: List[WatchlistEntry] = []
    with pathlib.Path(path).open("r", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            entries.append(
                WatchlistEntry(
                    symbol=row["symbol"],
                    enabled=row.get("enabled", "1") in {"1", "true", "True"},
                    leverage=int(row.get("leverage", 1)),
                    qty_mode=row.get("qty_mode", "fixed"),
                    qty_value=float(row.get("qty_value", 0)),
                    ema_period=int(row.get("ema_period", 50)),
                    supertrend_period=int(row.get("supertrend_period", 10)),
                    supertrend_multiplier=float(row.get("supertrend_multiplier", 3.0)),
                    trailing_mode=row.get("trailing_mode", "SUPERTREND"),
                    trailing_atr_mult=float(row.get("trailing_atr_mult", 2.0)),
                    trailing_pct=float(row.get("trailing_pct", 0.01)),
                    use_strategy_a=row.get("use_strategy_a", "1") in {"1", "true", "True"},
                    use_strategy_b=row.get("use_strategy_b", "0") in {"1", "true", "True"},
                    breakout_mode=row.get("breakout_mode", "standalone"),
                    range_window=int(row.get("range_window", 120)),
                    max_range_width_pct=float(row.get("max_range_width_pct", 0.006)),
                    retest_max_bars=int(row.get("retest_max_bars", 30)),
                )
            )
    return entries


def _to_candles(raw: List[Dict[str, float]]) -> List[Candle]:
    return [
        Candle(
            open_time=int(r["open_time"]),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            volume=float(r["volume"]),
            close_time=int(r["close_time"]),
        )
        for r in raw
    ]


async def _maybe_await(result):
    if asyncio.iscoroutine(result):
        return await result
    return result


def _persist_bot_state(md_engine: MarketDataEngine, store: CSVStore) -> None:
    rows = []
    for symbol, state in md_engine.symbols.items():
        rows.append(
            {
                "symbol": symbol,
                "state": state.b_state or "",
                "level": "" if state.b_level is None else str(state.b_level),
                "started_at_utc": "" if state.b_started_at is None else str(state.b_started_at),
                "bars_elapsed": "",
            }
        )
    store.write_all(rows)


def _restore_bot_state(md_engine: MarketDataEngine, store: CSVStore, watchlist: List[WatchlistEntry]) -> None:
    """Rehydrate Strategy B state machine so retests can continue after restart."""
    rows = store.read_all()
    watched = {w.symbol for w in watchlist}
    for row in rows:
        symbol = row.get("symbol")
        if not symbol or symbol not in watched:
            continue
        state = md_engine.ensure_symbol(symbol)
        state.b_state = row.get("state") or None
        state.b_level = float(row["level"]) if row.get("level") else None
        state.b_started_at = int(row["started_at_utc"]) if row.get("started_at_utc") else None


def build_adapter(cfg: AppConfig):
    if cfg.exchange.lower() == "binance":
        return BinanceFuturesAdapter(cfg.api_key or "", cfg.api_secret or "", testnet=cfg.mode.lower() == "testnet")
    if cfg.exchange.lower() == "delta":
        if not (cfg.api_key and cfg.api_secret):
            return MockDeltaAdapter()
        return DeltaExchangeAdapter(cfg.api_key, cfg.api_secret)
    raise ValueError(f"Unsupported exchange {cfg.exchange}")


def bootstrap_stores(cfg: AppConfig) -> Dict[str, CSVStore]:
    data_dir = pathlib.Path(cfg.data_dir)
    stores = {
        "positions": CSVStore(
            data_dir / "positions.csv",
            [
                "position_id",
                "symbol",
                "side",
                "qty",
                "entry_time_utc",
                "entry_price",
                "exit_time_utc",
                "exit_price",
                "status",
                "strategy",
                "stop_loss",
                "trailing_stop",
                "trailing_mode",
                "total_fees_usdt",
                "total_slippage_usdt",
                "realized_gross_pnl_usdt",
                "realized_net_pnl_usdt",
                "entry_notional_usdt",
                "exit_notional_usdt",
                "avg_notional_usdt",
                "gross_return_pct",
                "net_return_pct",
                "exit_reason",
                "last_update_utc",
            ],
        ),
        "trades": CSVStore(
            data_dir / "trades.csv",
            [
                "trade_id",
                "timestamp_utc",
                "exchange",
                "symbol",
                "side",
                "position_side",
                "qty",
                "price",
                "notional_usdt",
                "fee",
                "fee_asset",
                "fee_usdt",
                "order_id",
                "client_id",
                "reason",
                "expected_price",
                "slippage_usdt",
            ],
        ),
        "pnl_daily": CSVStore(
            data_dir / "pnl_daily.csv",
            [
                "date_utc",
                "gross_pnl_usdt",
                "net_pnl_usdt",
                "fees_usdt",
                "slippage_usdt",
                "traded_notional_usdt",
                "exit_notional_usdt",
                "trade_count",
                "win_count",
                "loss_count",
                "avg_win_usdt",
                "avg_loss_usdt",
                "profit_factor",
                "win_rate",
                "updated_at_utc",
            ],
        ),
        "signals": CSVStore(
            data_dir / "signals.csv",
            ["timestamp_utc", "symbol", "strategy", "signal", "price", "ema50", "st_dir", "st_value", "atr", "reason"],
        ),
        "errors": CSVStore(
            data_dir / "errors.csv",
            ["timestamp_utc", "module", "symbol", "error_type", "message"],
        ),
        "bot_state": CSVStore(
            data_dir / "bot_state.csv",
            ["symbol", "state", "level", "started_at_utc", "bars_elapsed"],
        ),
    }
    for store in stores.values():
        store.ensure_exists()
    return stores


def _process_exits(
    cfg: AppConfig,
    entry: WatchlistEntry,
    state: SymbolState,
    portfolio: Portfolio,
    exec_engine: ExecutionEngine,
    stores: Dict[str, CSVStore],
) -> None:
    """Evaluate exits for open positions on this symbol: SuperTrend flip, trailing stop, or ST stop hit."""
    if not state.candles:
        return
    latest = state.candles[-1]
    rows = stores["positions"].read_all()
    updated = False
    for row in rows:
        if row.get("status") != "OPEN" or row.get("symbol") != entry.symbol:
            continue
        side = row["side"].upper()
        trailing_mode = row.get("trailing_mode", entry.trailing_mode)
        prev_trail = float(row["trailing_stop"]) if row.get("trailing_stop") else None
        entry_price = float(row["entry_price"])
        trail_params = {"atr_mult": entry.trailing_atr_mult, "pct": entry.trailing_pct}
        new_trail, trail_hit = update_trailing_stop(
            side,
            trailing_mode,
            prev_trail,
            latest,
            entry_price,
            trail_params,
            state.atr_val,
            state.st_val,
        )
        row["trailing_stop"] = str(new_trail)

        # Strategy A stop ratchet on SuperTrend line
        if row.get("strategy") == "A" and state.st_val is not None and state.st_dir is not None:
            prev_stop = float(row["stop_loss"]) if row.get("stop_loss") else None
            if side == "LONG" and state.st_dir == 1:
                ratchet = max(prev_stop or state.st_val, state.st_val)
                row["stop_loss"] = str(ratchet)
                if latest.low <= ratchet:
                    trail_hit = True
            elif side == "SHORT" and state.st_dir == -1:
                ratchet = min(prev_stop or state.st_val, state.st_val)
                row["stop_loss"] = str(ratchet)
                if latest.high >= ratchet:
                    trail_hit = True

        st_flip = False
        if side == "LONG" and state.st_dir == -1:
            st_flip = True
        if side == "SHORT" and state.st_dir == 1:
            st_flip = True

        exit_reason: Optional[str] = None
        if st_flip:
            exit_reason = "ST_FLIP"
        elif trail_hit:
            exit_reason = "TRAIL_HIT"

        updated = True
        if exit_reason:
            stores["positions"].write_all(rows)
            portfolio.refresh()
            exec_engine.exit_position(cfg.exchange, row, latest.close, exit_reason)
            portfolio.refresh()
            # record signal
            stores["signals"].append(
                {
                    "timestamp_utc": utc_now().isoformat(),
                    "symbol": entry.symbol,
                    "strategy": row.get("strategy", ""),
                    "signal": "EXIT",
                    "price": str(latest.close),
                    "ema50": str(state.ema50 or ""),
                    "st_dir": str(state.st_dir or ""),
                    "st_value": str(state.st_val or ""),
                    "atr": str(state.atr_val or ""),
                    "reason": exit_reason,
                }
            )
            return

    if updated:
        stores["positions"].write_all(rows)
        portfolio.refresh()


def _process_entries(
    cfg: AppConfig,
    entry: WatchlistEntry,
    state: SymbolState,
    portfolio: Portfolio,
    exec_engine: ExecutionEngine,
    router: StrategyRouter,
    risk_manager: RiskManager,
    stores: Dict[str, CSVStore],
) -> None:
    """Evaluate entries only if no open position for symbol."""
    if not state.candles:
        return
    has_open = bool(portfolio.open_positions_for_symbol(entry.symbol))
    if has_open:
        return
    if not risk_manager.allow_new_position(len(portfolio.open_positions()), equity=1000):
        return
    signal = router.evaluate(state, entry)
    if not signal:
        return
    side = PositionSide.LONG if signal["action"] == "ENTER_LONG" else PositionSide.SHORT
    price = state.candles[-1].close
    qty = compute_qty(entry.qty_mode, entry.qty_value, price, equity=1000)
    # Enforce min notional
    min_notional = cfg.risk.min_order_notional_usdt
    if qty * price < min_notional:
        qty = min_notional / max(price, 1e-9)
    exec_engine.enter_position(
        exchange=cfg.exchange,
        symbol=entry.symbol,
        side=side,
        qty=qty,
        price=price,
        strategy=signal["strategy"],
        trailing_mode=entry.trailing_mode,
        stop_loss=float(signal.get("stop_loss", price)) if signal.get("stop_loss") else None,
    )
    portfolio.refresh()
    stores_signal = {
        "timestamp_utc": utc_now().isoformat(),
        "symbol": entry.symbol,
        "strategy": signal["strategy"],
        "signal": signal["action"],
        "price": str(price),
        "ema50": str(state.ema50 or ""),
        "st_dir": str(state.st_dir or ""),
        "st_value": str(state.st_val or ""),
        "atr": str(state.atr_val or ""),
        "reason": "",
    }
    stores["signals"].append(stores_signal)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crypto futures trading bot")
    parser.add_argument("--config", default="config.yaml.example", help="Path to config YAML")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    setup_logging()
    adapter = build_adapter(cfg)
    stores = bootstrap_stores(cfg)
    watchlist = [w for w in load_watchlist(cfg.watchlist_path) if w.enabled]
    if not watchlist:
        LOGGER.error("Empty watchlist")
        return 1
    md_engine = MarketDataEngine(cfg.universe_kline_lookback)
    router = StrategyRouter()
    risk_manager = RiskManager(cfg.risk)
    exec_engine = ExecutionEngine(
        trades_store=stores["trades"],
        positions_store=stores["positions"],
        pnl_store=stores["pnl_daily"],
        fees_bps=cfg.pnl.slippage_bps,
        slippage_bps=cfg.pnl.slippage_bps,
    )
    portfolio = Portfolio(stores["positions"])
    _restore_bot_state(md_engine, stores["bot_state"], watchlist)

    async def loop_once() -> None:
        now_ms = int(time.time() * 1000)
        for entry in watchlist:
            state = md_engine.ensure_symbol(entry.symbol)
            try:
                # Fetch full history on first pass, then only a small delta to reduce network load.
                fetch_limit = 500 if state.last_close_time is None else max(3, cfg.kline_refresh_seconds * 2)
                fetch_limit = min(cfg.universe_kline_lookback, fetch_limit)
                raw_klines = await _maybe_await(
                    adapter.get_klines(entry.symbol, interval="1m", limit=fetch_limit)
                )
                closed = [c for c in _to_candles(raw_klines) if c.close_time <= now_ms]
                if closed:
                    md_engine.update_candles(entry.symbol, closed, entry)
                    LOGGER.debug("Updated %s with %d closed candles; last close_time=%s", entry.symbol, len(closed), closed[-1].close_time)
                    if state.candles:
                        last = state.candles[-1]
                        LOGGER.debug(
                            "State %s: close=%.4f ema50=%.4f st=%.4f dir=%s atr=%.4f",
                            entry.symbol,
                            last.close,
                            state.ema50 or 0.0,
                            state.st_val or 0.0,
                            state.st_dir,
                            state.atr_val or 0.0,
                        )
                else:
                    LOGGER.debug("No closed candles returned for %s; check symbol/interval/testnet connectivity", entry.symbol)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.error("Kline fetch failed for %s: %s", entry.symbol, exc)
                stores["errors"].append(
                    {
                        "timestamp_utc": utc_now().isoformat(),
                        "module": "market_data",
                        "symbol": entry.symbol,
                        "error_type": "KLINE_FETCH",
                        "message": str(exc),
                    }
                )
                continue
            _process_exits(cfg, entry, state, portfolio, exec_engine, stores)
            _process_entries(cfg, entry, state, portfolio, exec_engine, router, risk_manager, stores)
        _persist_bot_state(md_engine, stores["bot_state"])

    async def run_loop() -> None:
        while True:
            await loop_once()
            await asyncio.sleep(cfg.poll_interval_seconds)

    LOGGER.info("Starting polling loop (scaffold).")
    asyncio.run(run_loop())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
