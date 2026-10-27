"""Liquidity eligibility based on reported volume and open interest."""

from __future__ import annotations

import pandas as pd


def apply_liquidity_filter(
    frame: pd.DataFrame,
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> pd.DataFrame:
    """Return pair rows marked eligible when both legs clear both thresholds."""
    if min_volume_lots < 0 or min_open_interest_lots < 0:
        raise ValueError("liquidity thresholds must be non-negative")
    required = {
        "left_volume_lots",
        "right_volume_lots",
        "left_open_interest_lots",
        "right_open_interest_lots",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing liquidity columns: {sorted(missing)}")

    filtered = frame.copy()
    filtered["liquid"] = (
        (filtered["left_volume_lots"] >= min_volume_lots)
        & (filtered["right_volume_lots"] >= min_volume_lots)
        & (filtered["left_open_interest_lots"] >= min_open_interest_lots)
        & (filtered["right_open_interest_lots"] >= min_open_interest_lots)
    )
    return filtered
