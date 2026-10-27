"""Build comparable, expiry-keyed gold-futures pair spreads."""

from __future__ import annotations

from itertools import combinations

import pandas as pd


REQUIRED_PRICE_COLUMNS = {
    "Symbol",
    "Date",
    "Expiry Date",
    "quote_price_per_gram",
    "purity_adjusted_price_per_gram",
    "Volume(Lots)",
    "Open Interest(Lots)",
}


def build_expiry_month_spreads(frame: pd.DataFrame) -> pd.DataFrame:
    """Return all six same-month spreads while retaining both true expiry dates.

    The source rows stay expiry-keyed.  A pair is joined only when both
    contracts trade on the same date and expire in the same calendar month;
    this supports the early-month GOLDM versus month-end contract gap without
    falsely labelling their distinct expiries as identical.
    """
    missing = REQUIRED_PRICE_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    prices = frame.copy()
    prices["Date"] = pd.to_datetime(prices["Date"])
    prices["Expiry Date"] = pd.to_datetime(prices["Expiry Date"])
    prices["expiry_month"] = prices["Expiry Date"].dt.to_period("M").astype(str)
    join_key = ["Symbol", "Date", "expiry_month"]
    if prices.duplicated(join_key).any():
        raise ValueError("multiple rows for a symbol, date, and expiry month")

    symbols = sorted(prices["Symbol"].unique())
    pairs: list[pd.DataFrame] = []
    for left_symbol, right_symbol in combinations(symbols, 2):
        left = _prepare_leg(prices[prices["Symbol"] == left_symbol], "left")
        right = _prepare_leg(prices[prices["Symbol"] == right_symbol], "right")
        paired = left.merge(right, on=["Date", "expiry_month"], how="inner", validate="one_to_one")
        if paired.empty:
            continue
        paired["left_symbol"] = left_symbol
        paired["right_symbol"] = right_symbol
        paired["spread_bps"] = (
            (paired["left_price_per_gram"] - paired["right_price_per_gram"])
            / paired["right_price_per_gram"]
            * 10_000
        )
        pairs.append(paired)

    if not pairs:
        return pd.DataFrame()
    return pd.concat(pairs, ignore_index=True).sort_values(
        ["left_symbol", "right_symbol", "left_expiry_date", "right_expiry_date", "Date"]
    ).reset_index(drop=True)


def _prepare_leg(prices: pd.DataFrame, side: str) -> pd.DataFrame:
    """Rename one contract leg for an unambiguous pair merge."""
    return prices[
        [
            "Date",
            "expiry_month",
            "Expiry Date",
            "quote_price_per_gram",
            "purity_adjusted_price_per_gram",
            "Volume(Lots)",
            "Open Interest(Lots)",
        ]
    ].rename(
        columns={
            "Expiry Date": f"{side}_expiry_date",
            "quote_price_per_gram": f"{side}_quote_price_per_gram",
            "purity_adjusted_price_per_gram": f"{side}_price_per_gram",
            "Volume(Lots)": f"{side}_volume_lots",
            "Open Interest(Lots)": f"{side}_open_interest_lots",
        }
    )
