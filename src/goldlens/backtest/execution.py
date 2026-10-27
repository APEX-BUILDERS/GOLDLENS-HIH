"""Execution timing helpers that prevent same-day fills."""

from __future__ import annotations

import pandas as pd


def next_trading_day_execution(signal_date: pd.Timestamp, trading_dates: pd.Series) -> pd.Timestamp | pd.NaT:
    """Return the first available execution date strictly after ``signal_date``."""
    dates = pd.to_datetime(trading_dates).dropna().drop_duplicates().sort_values()
    future_dates = dates[dates > pd.Timestamp(signal_date)]
    return future_dates.iloc[0] if not future_dates.empty else pd.NaT
