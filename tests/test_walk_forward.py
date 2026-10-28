from pathlib import Path

import pandas as pd

from goldlens.backtest.execution import next_trading_day_execution
from goldlens.backtest.lots import matched_whole_lots
from goldlens.backtest.walk_forward import walk_forward_backtest, walk_forward_decisions


def _spreads() -> pd.DataFrame:
    dates = pd.date_range("2025-03-24", periods=6, freq="B")
    return pd.DataFrame(
        {
            "left_symbol": ["GOLDM"] * 6,
            "right_symbol": ["GOLDTEN"] * 6,
            "left_expiry_date": pd.to_datetime(["2025-04-04"] * 6),
            "right_expiry_date": pd.to_datetime(["2025-04-30"] * 6),
            "Date": dates,
            "spread_bps": [1.0, 2.0, 8.0, 4.0, 7.0, 999.0],
            "liquid": [True] * 6,
            "left_price_per_gram": [1000.0] * 6,
            "right_price_per_gram": [1000.0] * 6,
        }
    )


def test_walkforward_uses_no_future_data() -> None:
    signals = _spreads()
    full = walk_forward_decisions(signals, window=3, min_periods=2, zscore_threshold=1.0)
    target_date = pd.Timestamp("2025-03-27")
    without_future = walk_forward_decisions(
        signals[signals["Date"] <= target_date], window=3, min_periods=2, zscore_threshold=1.0
    )

    full_target = full[full["Date"] == target_date].iloc[0]
    truncated_target = without_future[without_future["Date"] == target_date].iloc[0]
    assert full_target["zscore"] == truncated_target["zscore"]
    assert full_target["should_trade"] == truncated_target["should_trade"]


def test_execution_is_next_day() -> None:
    execution_date = next_trading_day_execution(
        pd.Timestamp("2025-03-25"), pd.Series(pd.to_datetime(["2025-03-24", "2025-03-25", "2025-03-27"]))
    )

    assert execution_date == pd.Timestamp("2025-03-27")


def test_lot_sizing_whole_lots() -> None:
    sizing = matched_whole_lots(
        left_price_per_gram=1000.0,
        right_price_per_gram=1000.0,
        left_lot_grams=100.0,
        right_lot_grams=10.0,
        target_notional=200_000.0,
    )

    assert (sizing.left_lots, sizing.right_lots) == (2, 20)
    assert sizing.left_notional == sizing.right_notional == 200_000.0


def test_backtest_excludes_trade_that_crosses_train_test_boundary() -> None:
    spreads = _spreads().iloc[:5].copy()
    spreads["spread_bps"] = [1.0, 2.0, 8.0, 4.0, 5.0]
    trades = walk_forward_backtest(
        spreads,
        {"GOLDM": {"lot_unit_grams": 1.0}, "GOLDTEN": {"lot_unit_grams": 1.0}},
        window=3,
        min_periods=2,
        zscore_threshold=1.0,
        target_notional=1_000.0,
        train_end=pd.Timestamp("2025-03-26"),
    )

    assert trades.empty
