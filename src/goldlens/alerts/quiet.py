"""Create quiet, non-predictive watches from materialized past-only signals."""

from __future__ import annotations

import pandas as pd


ALERT_COLUMNS = [
    "alert_date",
    "left_symbol",
    "left_expiry_date",
    "right_symbol",
    "right_expiry_date",
    "spread_bps",
    "zscore",
    "signal_direction",
    "alert_type",
    "message",
]
REQUIRED_COLUMNS = {
    "Date",
    "left_symbol",
    "left_expiry_date",
    "right_symbol",
    "right_expiry_date",
    "spread_bps",
    "zscore",
    "liquid",
}


def build_quiet_alerts(
    signals: pd.DataFrame,
    zscore_threshold: float,
    as_of_date: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    """Return watches for the newest observed date without external notification.

    Inputs are the already materialized, past-only S4 z-scores. The function
    never calculates a future price, selects an execution date, or submits an
    order: an alert is a research watch, not a prediction or trading signal.
    """
    if zscore_threshold <= 0:
        raise ValueError("zscore_threshold must be positive")
    missing = REQUIRED_COLUMNS - set(signals.columns)
    if missing:
        raise ValueError(f"missing alert signal columns: {sorted(missing)}")
    if signals.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    dates = pd.to_datetime(signals["Date"])
    as_of = dates.max() if as_of_date is None else pd.Timestamp(as_of_date)
    available = signals.loc[dates <= as_of].copy()
    latest = available.loc[pd.to_datetime(available["Date"]) == as_of].copy()
    watches = latest.loc[latest["liquid"] & latest["zscore"].abs().ge(zscore_threshold)].copy()
    watches["alert_date"] = as_of
    watches["signal_direction"] = "short_left_long_right"
    watches.loc[watches["zscore"] < 0, "signal_direction"] = "long_left_short_right"
    watches["alert_type"] = "liquid_spread_deviation_watch"
    watches["message"] = "Research watch only; not a price prediction, execution instruction, or profit claim."
    return watches[ALERT_COLUMNS].sort_values("zscore", key=lambda column: column.abs(), ascending=False).reset_index(drop=True)
