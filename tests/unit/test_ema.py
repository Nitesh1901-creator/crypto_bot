from src.indicators.ema import ema


def test_ema_basic():
    vals = ema([1, 2, 3, 4, 5], 3)
    assert len(vals) == 5
    assert vals[-1] > vals[0]
