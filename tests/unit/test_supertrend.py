from src.indicators.supertrend import supertrend


def test_supertrend_basic():
    highs = [2, 3, 4, 5, 6]
    lows = [1, 1, 2, 3, 4]
    closes = [1.5, 2.5, 3.5, 4.5, 5.5]
    st_vals, dirs = supertrend(highs, lows, closes, 2, 3.0)
    assert len(st_vals) == len(closes)
    assert len(dirs) == len(closes)
    assert dirs[-1] in (-1, 1)
