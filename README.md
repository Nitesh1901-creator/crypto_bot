# Crypto Futures Trading Bot (Scaffold)

Python 3.11+ CLI bot for Binance USDT-M Futures (testnet/live) and Delta Exchange (scaffold/mock). Uses CSV-only persistence, 1m closed candles, and SuperTrend/EMA + breakout-retest strategies.

## Features & Constraints
- 1m closed-candle signals; LONG/SHORT
- Strategies: (A) SuperTrend line cross EMA50; (B) Breakout/Breakdown + retest
- Trailing stop modes: ATR/PCT/SUPERTREND (per watchlist)
- CSV-only persistence (positions, trades, pnl_daily, signals, errors, bot_state, watchlist)
- Safety: default testnet; live requires `confirm_live=true`

## Quickstart
1) Python 3.11+, create venv.
2) Install deps: `pip install -r requirements.txt`
3) Copy `config.yaml.example` to `config.yaml`; set keys/env. Copy `.env.example` if preferred.
4) Edit `watchlist.csv.example` for symbols/sizing/strategy flags.
5) Run (scaffold loop placeholder; implement adapter calls before live):
```
python -m src.main --config config.yaml
```

## Structure
- `src/main.py` — CLI entry; wires config, stores, adapters, router, risk, execution.
- `src/config/loader.py` — YAML/env config loader with live safety.
- `src/datastore/csv_store.py` — Atomic CSV storage with simple locks.
- `src/indicators/` — EMA, ATR, SuperTrend.
- `src/market_data/engine.py` — Closed-candle buffer + indicators.
- `src/strategy/` — Strategy A (ST line cross EMA), Strategy B (breakout+retest), router.
- `src/levels/range_detector.py` — Range detection helper.
- `src/exchanges/` — Base interface; Binance/Delta scaffolds; mock adapter.
- `src/execution/engine.py` — Trade/position recording skeleton.
- `src/risk/` — Risk manager and sizing helpers.
- `src/pnl/calculator.py` — PnL and daily bucketing.
- `watchlist.csv.example`, `config.yaml.example`, `.env.example`, `requirements.txt`
- Tests: basic indicator unit tests under `tests/unit`.

## TODO before production
- Implement Binance/Delta REST/WebSocket calls, rate limits, retries, and symbol filters.
- Finish exit handling with SuperTrend flips + trailing stops wired to positions/trades.
- Flesh out integration tests with Binance testnet (long/short open/close, CSV assertions).
- Expand PnL daily stats rebuild on startup and reconcile multiple fills/VWAP.
- Add signal/error/bot_state writers and Strategy B state machine persistence.
- Harden file locking and concurrency if multi-process.
