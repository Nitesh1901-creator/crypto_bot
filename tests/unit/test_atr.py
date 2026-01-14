from src.indicators.atr import atr


def test_atr_basic():
    highs = [2, 3, 4, 5]
    lows = [1, 1, 2, 3]
    closes = [1.5, 2, 3, 4]
    vals = atr(highs, lows, closes, 2)
    assert len(vals) == 4
    assert vals[-1] > 0
