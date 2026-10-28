import pandas as pd

from goldlens.backtest.costs import apply_trading_costs


RATES = {
    "brokerage_rate": 0.0001,
    "exchange_charge_rate": 0.0002,
    "ctt_rate": 0.0001,
    "gst_rate": 0.18,
    "stamp_duty_rate": 0.0001,
    "slippage_bps": {"GOLDM": 1.0, "GOLDTEN": 1.0},
    "margin_rate": 0.12,
    "thin_day_haircut_bps": {"GOLDM": 5.0, "GOLDTEN": 5.0},
    "brokerage_cap_per_order": 20.0,
    "sebi_fee_per_crore": 10.0,
}


def _trades(volume: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "direction": ["short_left_long_right"],
            "left_symbol": ["GOLDM"],
            "right_symbol": ["GOLDTEN"],
            "execution_date": pd.to_datetime(["2025-03-31"]),
            "exit_date": pd.to_datetime(["2025-04-01"]),
            "gross_pnl": [1000.0],
            "left_entry_notional": [100_000.0],
            "right_entry_notional": [100_000.0],
            "left_exit_notional": [101_000.0],
            "right_exit_notional": [99_000.0],
            "left_entry_volume_lots": [volume],
            "right_entry_volume_lots": [10],
            "left_entry_open_interest_lots": [20],
            "right_entry_open_interest_lots": [20],
        }
    )


def test_net_return_below_gross() -> None:
    costed = apply_trading_costs(_trades(), RATES, min_volume_lots=1, min_open_interest_lots=1)

    assert costed.loc[0, "total_cost"] > 0
    assert costed.loc[0, "net_pnl"] < costed.loc[0, "gross_pnl"]


def test_thin_day_haircut_applied() -> None:
    liquid = apply_trading_costs(_trades(), RATES, min_volume_lots=1, min_open_interest_lots=1)
    thin = apply_trading_costs(_trades(volume=0), RATES, min_volume_lots=1, min_open_interest_lots=1)

    assert not liquid.loc[0, "thin_day"]
    assert thin.loc[0, "thin_day"]
    assert thin.loc[0, "thin_day_haircut_cost"] > 0
    assert thin.loc[0, "net_pnl"] < liquid.loc[0, "net_pnl"]


def test_brokerage_is_capped_per_executed_order() -> None:
    rates = {**RATES, "brokerage_rate": 0.0003}
    costed = apply_trading_costs(_trades(), rates, min_volume_lots=1, min_open_interest_lots=1)

    assert costed.loc[0, "brokerage_cost"] == 80.0
    assert costed.loc[0, "brokerage_cost"] < costed.loc[0, "round_trip_turnover"] * rates["brokerage_rate"]


def test_sebi_fee_is_rs_10_per_crore_of_turnover() -> None:
    costed = apply_trading_costs(_trades(), RATES, min_volume_lots=1, min_open_interest_lots=1)

    assert costed.loc[0, "round_trip_turnover"] == 400_000.0
    assert costed.loc[0, "sebi_fee"] == 0.4
