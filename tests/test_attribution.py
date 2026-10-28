import pandas as pd

from goldlens.backtest.attribution import build_attribution_tables


def _costed_trades() -> pd.DataFrame:
    rows = []
    for scenario, cost in (("low", 10.0), ("base", 20.0)):
        rows.append(
            {
                "scenario": scenario,
                "phase": "out_of_sample",
                "left_symbol": "GOLDM",
                "left_expiry_date": pd.Timestamp("2025-04-04"),
                "right_symbol": "GOLDTEN",
                "right_expiry_date": pd.Timestamp("2025-04-30"),
                "direction": "short_left_long_right",
                "gross_pnl": 100.0,
                "total_cost": cost,
                "net_pnl": 100.0 - cost,
                "left_entry_notional": 1_000.0,
                "right_entry_notional": 1_000.0,
                "brokerage_cost": cost,
                "exchange_charge_cost": 0.0,
                "sebi_fee": 0.0,
                "gst_cost": 0.0,
                "ctt_cost": 0.0,
                "stamp_duty_cost": 0.0,
                "margin_cost": 0.0,
                "slippage_cost": 0.0,
                "thin_day_haircut_cost": 0.0,
            }
        )
    return pd.DataFrame(rows)


def test_attribution_reconciles_costs_and_net_pnl() -> None:
    tables = build_attribution_tables(_costed_trades())
    base = tables["overall"].loc[lambda frame: frame["scenario"] == "base"].iloc[0]

    assert base["trades"] == 1
    assert base["gross_pnl"] == 100.0
    assert base["total_cost"] == 20.0
    assert base["net_pnl"] == 80.0
    assert base["cost_reconciliation"] == 0.0
    assert base["pnl_reconciliation"] == 0.0


def test_expiry_pair_attribution_retains_exact_expiries() -> None:
    expiry_pair = build_attribution_tables(_costed_trades())["expiry_pair"]

    assert set(expiry_pair["left_expiry_date"]) == {pd.Timestamp("2025-04-04")}
    assert set(expiry_pair["right_expiry_date"]) == {pd.Timestamp("2025-04-30")}
