from src.market_data.engine import Candle
from src.strategy.trailing import update_trailing_stop


def test_trailing_atr_long_moves_up_only():
    candle1 = Candle(0, 100, 110, 95, 105, 0, 0)
    trail, hit = update_trailing_stop("LONG", "ATR", None, candle1, 100, {"atr_mult": 2.0}, atr_value=2.5, supertrend_value=None)
    assert not hit
    candle2 = Candle(0, 110, 115, 105, 112, 0, 0)
    trail2, _ = update_trailing_stop("LONG", "ATR", trail, candle2, 100, {"atr_mult": 2.0}, atr_value=2.0, supertrend_value=None)
    assert trail2 >= trail


def test_trailing_pct_short_moves_down_only():
    candle1 = Candle(0, 100, 105, 90, 92, 0, 0)
    trail, hit = update_trailing_stop("SHORT", "PCT", None, candle1, 100, {"pct": 0.02}, atr_value=None, supertrend_value=None)
    assert not hit
    candle2 = Candle(0, 90, 95, 80, 85, 0, 0)
    trail2, _ = update_trailing_stop("SHORT", "PCT", trail, candle2, 100, {"pct": 0.02}, atr_value=None, supertrend_value=None)
    assert trail2 <= trail


def test_trailing_stops_hit():
    candle1 = Candle(0, 100, 110, 95, 105, 0, 0)
    trail, hit = update_trailing_stop("LONG", "SUPERTREND", None, candle1, 100, {}, atr_value=None, supertrend_value=101)
    assert not hit
    candle2 = Candle(0, 100, 102, 99, 100, 0, 0)
    _, hit2 = update_trailing_stop("LONG", "SUPERTREND", trail, candle2, 100, {}, atr_value=None, supertrend_value=101)
    assert hit2
