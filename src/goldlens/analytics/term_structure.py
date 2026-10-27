"""Expiry-keyed term structure and spread decomposition utilities."""

from __future__ import annotations

import pandas as pd


TERM_REQUIRED_COLUMNS = {
    "Symbol",
    "Date",
    "Expiry Date",
    "purity_adjusted_price_per_gram",
}


def build_term_structure(frame: pd.DataFrame) -> pd.DataFrame:
    """Add days-to-expiry and same-day local curve slopes to expiry-keyed prices.

    Slopes use only other expiries observed on the same trade date and within
    the same symbol.  No prior or future trade dates are used.
    """
    missing = TERM_REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"missing term-structure columns: {sorted(missing)}")

    structure = frame.copy()
    structure["Date"] = pd.to_datetime(structure["Date"])
    structure["Expiry Date"] = pd.to_datetime(structure["Expiry Date"])
    structure["days_to_expiry"] = (structure["Expiry Date"] - structure["Date"]).dt.days
    if (structure["days_to_expiry"] < 0).any():
        raise ValueError("term structure cannot contain expired rows")
    if structure.duplicated(["Symbol", "Date", "Expiry Date"]).any():
        raise ValueError("term structure rows must be unique per symbol, date, and expiry")

    structure = structure.sort_values(["Symbol", "Date", "Expiry Date"]).reset_index(drop=True)
    structure["curve_slope_per_gram_per_day"] = float("nan")
    for _, indices in structure.groupby(["Symbol", "Date"], sort=False).groups.items():
        group = structure.loc[indices]
        structure.loc[indices, "curve_slope_per_gram_per_day"] = _local_curve_slope(group).to_numpy()
    return structure


def add_spread_decomposition(spreads: pd.DataFrame, term_structure: pd.DataFrame) -> pd.DataFrame:
    """Decompose quote spread into purity, carry/roll-down, and residual.

    The carry/roll-down component is the local left-leg curve slope multiplied
    by the true expiry-day gap.  For each row, the components exactly sum to
    ``raw_spread_per_gram`` when a same-day curve slope is available.
    """
    required_spread_columns = {
        "left_symbol",
        "right_symbol",
        "Date",
        "left_expiry_date",
        "right_expiry_date",
        "left_quote_price_per_gram",
        "right_quote_price_per_gram",
        "left_price_per_gram",
        "right_price_per_gram",
    }
    missing = required_spread_columns - set(spreads.columns)
    if missing:
        raise ValueError(f"missing spread columns: {sorted(missing)}")

    slope_rows = term_structure[
        ["Symbol", "Date", "Expiry Date", "curve_slope_per_gram_per_day"]
    ].rename(
        columns={
            "Symbol": "left_symbol",
            "Expiry Date": "left_expiry_date",
        }
    )
    decomposed = spreads.merge(
        slope_rows,
        on=["left_symbol", "Date", "left_expiry_date"],
        how="left",
        validate="many_to_one",
    )
    decomposed["raw_spread_per_gram"] = (
        decomposed["left_quote_price_per_gram"] - decomposed["right_quote_price_per_gram"]
    )
    normalized_spread = (
        decomposed["left_price_per_gram"] - decomposed["right_price_per_gram"]
    )
    decomposed["purity_component_per_gram"] = (
        decomposed["raw_spread_per_gram"] - normalized_spread
    )
    expiry_gap_days = (
        pd.to_datetime(decomposed["right_expiry_date"])
        - pd.to_datetime(decomposed["left_expiry_date"])
    ).dt.days
    decomposed["carry_roll_down_component_per_gram"] = -(
        decomposed["curve_slope_per_gram_per_day"] * expiry_gap_days
    )
    decomposed["residual_component_per_gram"] = (
        decomposed["raw_spread_per_gram"]
        - decomposed["purity_component_per_gram"]
        - decomposed["carry_roll_down_component_per_gram"]
    )
    return decomposed


def _local_curve_slope(group: pd.DataFrame) -> pd.Series:
    """Estimate each point's slope from its closest adjacent expiry."""
    expiry_days = group["days_to_expiry"].to_numpy()
    prices = group["purity_adjusted_price_per_gram"].to_numpy()
    slopes: list[float] = []
    for index in range(len(group)):
        if len(group) < 2:
            slopes.append(float("nan"))
            continue
        neighbour = 1 if index == 0 else index - 1
        day_gap = expiry_days[neighbour] - expiry_days[index]
        slopes.append((prices[neighbour] - prices[index]) / day_gap)
    return pd.Series(slopes, index=group.index)
