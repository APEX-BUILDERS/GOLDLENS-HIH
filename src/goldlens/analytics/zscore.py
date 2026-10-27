"""Past-only rolling z-scores for expiry-keyed spreads."""

from __future__ import annotations

import pandas as pd


SPREAD_SERIES_KEY = ["left_symbol", "right_symbol", "left_expiry_date", "right_expiry_date"]


def add_past_only_rolling_zscore(
    frame: pd.DataFrame,
    window: int,
    min_periods: int,
) -> pd.DataFrame:
    """Add a z-score whose mean and standard deviation exclude the current day.

    Each unique pair of actual expiries is calculated independently.  The
    current spread is scored against only preceding rows in that same series;
    future rows never affect an earlier signal.
    """
    if window < 2 or min_periods < 2 or min_periods > window:
        raise ValueError("require 2 <= min_periods <= window")
    required = set(SPREAD_SERIES_KEY) | {"Date", "spread_bps"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing spread columns: {sorted(missing)}")

    scored = frame.copy().sort_values(SPREAD_SERIES_KEY + ["Date"])
    if scored.duplicated(SPREAD_SERIES_KEY + ["Date"]).any():
        raise ValueError("spread rows must be unique per pair, expiries, and date")
    grouped = scored.groupby(SPREAD_SERIES_KEY, group_keys=False, sort=False)
    scored["rolling_mean_bps"] = grouped["spread_bps"].transform(
        lambda values: values.shift(1).rolling(window=window, min_periods=min_periods).mean()
    )
    scored["rolling_std_bps"] = grouped["spread_bps"].transform(
        lambda values: values.shift(1).rolling(window=window, min_periods=min_periods).std(ddof=0)
    )
    scored["zscore"] = (
        (scored["spread_bps"] - scored["rolling_mean_bps"])
        / scored["rolling_std_bps"].where(scored["rolling_std_bps"] != 0)
    )
    return scored.reset_index(drop=True)
