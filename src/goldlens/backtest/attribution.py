"""Expiry-keyed attribution for costed walk-forward trades."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


COST_COLUMNS = (
    "brokerage_cost",
    "exchange_charge_cost",
    "sebi_fee",
    "gst_cost",
    "ctt_cost",
    "stamp_duty_cost",
    "margin_cost",
    "slippage_cost",
    "thin_day_haircut_cost",
)
REQUIRED_COLUMNS = {
    "scenario",
    "phase",
    "gross_pnl",
    "net_pnl",
    "total_cost",
    "left_entry_notional",
    "right_entry_notional",
    *COST_COLUMNS,
}


def summarize_attribution(trades: pd.DataFrame, group_columns: Sequence[str]) -> pd.DataFrame:
    """Aggregate real costed trades and retain P&L and cost reconciliation.

    ``group_columns`` must retain the desired expiry keys for a drill-down. No
    prices, signals, or series are recomputed, so attribution cannot alter the
    past-only S7 decision or next-day execution rules.
    """
    missing = REQUIRED_COLUMNS - set(trades.columns)
    if missing:
        raise ValueError(f"missing attributed trade columns: {sorted(missing)}")
    absent_groups = set(group_columns) - set(trades.columns)
    if absent_groups:
        raise ValueError(f"missing attribution grouping columns: {sorted(absent_groups)}")

    source = trades.copy()
    source["entry_exposure"] = source["left_entry_notional"] + source["right_entry_notional"]
    aggregation = {
        "trades": ("gross_pnl", "size"),
        "gross_pnl": ("gross_pnl", "sum"),
        "total_cost": ("total_cost", "sum"),
        "net_pnl": ("net_pnl", "sum"),
        "entry_exposure": ("entry_exposure", "sum"),
        **{column: (column, "sum") for column in COST_COLUMNS},
    }
    summary = source.groupby(list(group_columns), dropna=False, as_index=False).agg(**aggregation)
    summary["gross_return"] = summary["gross_pnl"] / summary["entry_exposure"]
    summary["net_return"] = summary["net_pnl"] / summary["entry_exposure"]
    summary["cost_reconciliation"] = summary[list(COST_COLUMNS)].sum(axis=1) - summary["total_cost"]
    summary["pnl_reconciliation"] = summary["gross_pnl"] - summary["total_cost"] - summary["net_pnl"]
    return summary.sort_values(list(group_columns)).reset_index(drop=True)


def build_attribution_tables(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build overall, phase, and exact-expiry-pair attribution tables."""
    return {
        "overall": summarize_attribution(trades, ["scenario"]),
        "phase": summarize_attribution(trades, ["scenario", "phase"]),
        "expiry_pair": summarize_attribution(
            trades,
            [
                "scenario",
                "phase",
                "left_symbol",
                "left_expiry_date",
                "right_symbol",
                "right_expiry_date",
                "direction",
            ],
        ),
    }
