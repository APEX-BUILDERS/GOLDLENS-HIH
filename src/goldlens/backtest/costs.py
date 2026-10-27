"""Config-driven costs and liquidity haircuts for held futures contracts."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PUBLISHED_RATE_KEYS = {
    "brokerage_rate",
    "brokerage_cap_per_order",
    "exchange_charge_rate",
    "sebi_fee_per_crore",
    "ctt_rate",
    "gst_rate",
    "stamp_duty_rate",
}
SCENARIO_RATE_KEYS = {
    "slippage_bps",
    "margin_rate",
    "thin_day_haircut_bps",
}
RATE_KEYS = PUBLISHED_RATE_KEYS | SCENARIO_RATE_KEYS


def load_cost_scenarios(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load published inputs and explicit low, base, and high assumptions."""
    with Path(path).open(encoding="utf-8") as stream:
        payload = yaml.safe_load(stream) or {}
    published = payload.get("published_costs", {})
    missing = PUBLISHED_RATE_KEYS - set(published)
    scenarios = payload.get("scenarios", {})
    if missing or set(scenarios) != {"low", "base", "high"}:
        raise ValueError("cost configuration needs published rates and low/base/high scenarios")
    return {
        name: {
            **{key: published[key]["value"] for key in PUBLISHED_RATE_KEYS},
            **{key: scenario[key]["value"] for key in SCENARIO_RATE_KEYS},
        }
        for name, scenario in scenarios.items()
    }


def apply_trading_costs(
    trades: pd.DataFrame,
    rates: Mapping[str, Any],
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> pd.DataFrame:
    """Add contract-held costs, thin-day haircuts, gross and net P&L.

    CTT is charged once on the selling leg of each contract.  Brokerage,
    exchange charges and slippage apply to full entry-and-exit turnover. GST
    applies to the brokerage plus exchange service charges. ``margin_rate`` is
    an annual financing rate applied to entry notional over calendar holding
    days. Thin-day haircuts apply only when either entry leg misses a threshold.
    """
    if min_volume_lots < 0 or min_open_interest_lots < 0:
        raise ValueError("liquidity thresholds must be non-negative")
    missing_rates = RATE_KEYS - set(rates)
    if missing_rates:
        raise ValueError(f"missing cost rates: {sorted(missing_rates)}")
    required = {
        "direction",
        "execution_date",
        "exit_date",
        "gross_pnl",
        "left_entry_notional",
        "right_entry_notional",
        "left_exit_notional",
        "right_exit_notional",
        "left_entry_volume_lots",
        "right_entry_volume_lots",
        "left_entry_open_interest_lots",
        "right_entry_open_interest_lots",
    }
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"missing trade columns: {sorted(missing)}")

    costed = trades.copy()
    costed["round_trip_turnover"] = (
        costed["left_entry_notional"]
        + costed["right_entry_notional"]
        + costed["left_exit_notional"]
        + costed["right_exit_notional"]
    )
    leg_notionals = ["left_entry_notional", "right_entry_notional", "left_exit_notional", "right_exit_notional"]
    costed["brokerage_cost"] = sum(
        (costed[column] * float(rates["brokerage_rate"])).clip(
            upper=float(rates["brokerage_cap_per_order"])
        )
        for column in leg_notionals
    )
    costed["exchange_charge_cost"] = (
        costed["round_trip_turnover"] * float(rates["exchange_charge_rate"])
    )
    costed["sebi_fee"] = costed["round_trip_turnover"] * float(rates["sebi_fee_per_crore"]) / 10_000_000
    costed["gst_cost"] = (costed["brokerage_cost"] + costed["exchange_charge_cost"] + costed["sebi_fee"]) * float(rates["gst_rate"])
    left_sale_notional = costed["left_entry_notional"].where(
        costed["direction"] == "short_left_long_right", costed["left_exit_notional"]
    )
    right_sale_notional = costed["right_entry_notional"].where(
        costed["direction"] == "long_left_short_right", costed["right_exit_notional"]
    )
    costed["ctt_cost"] = (left_sale_notional + right_sale_notional) * float(rates["ctt_rate"])
    left_buy = costed["left_entry_notional"].where(costed["direction"] == "long_left_short_right", costed["left_exit_notional"])
    right_buy = costed["right_entry_notional"].where(costed["direction"] == "short_left_long_right", costed["right_exit_notional"])
    costed["stamp_duty_cost"] = (left_buy + right_buy) * float(rates["stamp_duty_rate"])
    holding_days = (pd.to_datetime(costed["exit_date"]) - pd.to_datetime(costed["execution_date"])).dt.days
    costed["margin_cost"] = (
        (costed["left_entry_notional"] + costed["right_entry_notional"])
        * float(rates["margin_rate"])
        * holding_days
        / 365
    )
    left_turnover = costed["left_entry_notional"] + costed["left_exit_notional"]
    right_turnover = costed["right_entry_notional"] + costed["right_exit_notional"]
    costed["slippage_cost"] = (left_turnover * costed["left_symbol"].map(rates["slippage_bps"]) + right_turnover * costed["right_symbol"].map(rates["slippage_bps"])) / 10_000
    costed["thin_day"] = (
        (costed["left_entry_volume_lots"] < min_volume_lots)
        | (costed["right_entry_volume_lots"] < min_volume_lots)
        | (costed["left_entry_open_interest_lots"] < min_open_interest_lots)
        | (costed["right_entry_open_interest_lots"] < min_open_interest_lots)
    )
    costed["thin_day_haircut_cost"] = (
        (left_turnover * costed["left_symbol"].map(rates["thin_day_haircut_bps"]) + right_turnover * costed["right_symbol"].map(rates["thin_day_haircut_bps"])) / 10_000
    ).where(costed["thin_day"], 0.0)
    cost_columns = [
        "brokerage_cost",
        "exchange_charge_cost",
        "sebi_fee",
        "gst_cost",
        "ctt_cost",
        "stamp_duty_cost",
        "margin_cost",
        "slippage_cost",
        "thin_day_haircut_cost",
    ]
    costed["total_cost"] = costed[cost_columns].sum(axis=1)
    costed["net_pnl"] = costed["gross_pnl"] - costed["total_cost"]
    exposure = costed["left_entry_notional"] + costed["right_entry_notional"]
    costed["gross_return"] = costed["gross_pnl"] / exposure
    costed["net_return"] = costed["net_pnl"] / exposure
    return costed
