"""Expiry-keyed, past-only walk-forward backtesting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

import pandas as pd

from goldlens.analytics.zscore import SPREAD_SERIES_KEY, add_past_only_rolling_zscore
from goldlens.backtest.execution import next_trading_day_execution
from goldlens.backtest.lots import matched_whole_lots


def walk_forward_decisions(
    spreads: pd.DataFrame,
    window: int,
    min_periods: int,
    zscore_threshold: float,
) -> pd.DataFrame:
    """Recompute past-only scores and decide signals without using future rows."""
    if zscore_threshold <= 0:
        raise ValueError("zscore_threshold must be positive")
    required = {"Date", "liquid", "spread_bps"} | set(SPREAD_SERIES_KEY)
    missing = required - set(spreads.columns)
    if missing:
        raise ValueError(f"missing walk-forward columns: {sorted(missing)}")
    decisions = add_past_only_rolling_zscore(spreads, window, min_periods)
    decisions["should_trade"] = decisions["liquid"] & (decisions["zscore"].abs() >= zscore_threshold)
    decisions["direction"] = pd.NA
    decisions.loc[decisions["should_trade"] & (decisions["zscore"] > 0), "direction"] = "short_left_long_right"
    decisions.loc[decisions["should_trade"] & (decisions["zscore"] < 0), "direction"] = "long_left_short_right"
    return decisions


def walk_forward_backtest(
    spreads: pd.DataFrame,
    contracts: Mapping[str, Mapping[str, Any]],
    window: int,
    min_periods: int,
    zscore_threshold: float,
    target_notional: float,
    train_end: pd.Timestamp,
) -> pd.DataFrame:
    """Replay signals chronologically with next-day entry and following-day exit.

    Scores are recalculated from preceding observations only.  A row's outcome
    uses later prices solely to evaluate an already-fixed signal, never to form
    that signal.  ``train_end`` separates in-sample and unseen out-of-sample
    signal dates.
    """
    required = {
        "left_symbol",
        "right_symbol",
        "left_price_per_gram",
        "right_price_per_gram",
    }
    missing = required - set(spreads.columns)
    if missing:
        raise ValueError(f"missing execution columns: {sorted(missing)}")
    decisions = walk_forward_decisions(spreads, window, min_periods, zscore_threshold)
    rows: list[dict[str, Any]] = []
    for _, signal in decisions[decisions["should_trade"]].iterrows():
        series = decisions[
            (decisions[SPREAD_SERIES_KEY] == signal[SPREAD_SERIES_KEY]).all(axis=1)
        ].sort_values("Date")
        execution_date = next_trading_day_execution(signal["Date"], series["Date"])
        if pd.isna(execution_date):
            continue
        exit_date = next_trading_day_execution(execution_date, series["Date"])
        if pd.isna(exit_date):
            continue
        # A phase must contain an outcome observed entirely on its own side of
        # the train boundary.  In particular, a pre-cutoff signal cannot use
        # a post-cutoff entry or exit price in an in-sample result.
        signal_is_in_sample = signal["Date"] <= pd.Timestamp(train_end)
        outcome_is_in_sample = execution_date <= pd.Timestamp(train_end) and exit_date <= pd.Timestamp(train_end)
        if signal_is_in_sample != outcome_is_in_sample:
            continue
        entry = series.loc[series["Date"] == execution_date].iloc[0]
        exit_row = series.loc[series["Date"] == exit_date].iloc[0]
        sizing = matched_whole_lots(
            entry["left_price_per_gram"],
            entry["right_price_per_gram"],
            contracts[signal["left_symbol"]]["lot_unit_grams"],
            contracts[signal["right_symbol"]]["lot_unit_grams"],
            target_notional,
        )
        if sizing.left_lots == 0:
            continue
        left_sign, right_sign = (-1, 1) if signal["direction"] == "short_left_long_right" else (1, -1)
        gross_pnl = (
            left_sign
            * sizing.left_lots
            * contracts[signal["left_symbol"]]["lot_unit_grams"]
            * (exit_row["left_price_per_gram"] - entry["left_price_per_gram"])
            + right_sign
            * sizing.right_lots
            * contracts[signal["right_symbol"]]["lot_unit_grams"]
            * (exit_row["right_price_per_gram"] - entry["right_price_per_gram"])
        )
        left_entry_notional = sizing.left_notional
        right_entry_notional = sizing.right_notional
        left_exit_notional = (
            sizing.left_lots
            * contracts[signal["left_symbol"]]["lot_unit_grams"]
            * exit_row["left_price_per_gram"]
        )
        right_exit_notional = (
            sizing.right_lots
            * contracts[signal["right_symbol"]]["lot_unit_grams"]
            * exit_row["right_price_per_gram"]
        )
        rows.append(
            {
                **{key: signal[key] for key in SPREAD_SERIES_KEY},
                "signal_date": signal["Date"],
                "execution_date": execution_date,
                "exit_date": exit_date,
                "direction": signal["direction"],
                "zscore": signal["zscore"],
                **asdict(sizing),
                "left_entry_notional": left_entry_notional,
                "right_entry_notional": right_entry_notional,
                "left_exit_notional": left_exit_notional,
                "right_exit_notional": right_exit_notional,
                "left_entry_volume_lots": entry["left_volume_lots"],
                "right_entry_volume_lots": entry["right_volume_lots"],
                "left_entry_open_interest_lots": entry["left_open_interest_lots"],
                "right_entry_open_interest_lots": entry["right_open_interest_lots"],
                "gross_pnl": gross_pnl,
                "phase": "in_sample" if signal_is_in_sample else "out_of_sample",
            }
        )
    return pd.DataFrame(rows)


def summarize_backtest(trades: pd.DataFrame) -> pd.DataFrame:
    """Return gross results separately for in-sample and out-of-sample trades."""
    if trades.empty:
        return pd.DataFrame(columns=["phase", "trades", "gross_pnl"])
    return (
        trades.groupby("phase", as_index=False)
        .agg(trades=("gross_pnl", "size"), gross_pnl=("gross_pnl", "sum"))
        .sort_values("phase")
        .reset_index(drop=True)
    )
