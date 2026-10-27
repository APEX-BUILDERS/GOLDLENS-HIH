"""Normalize expiry-keyed MCX futures prices to a common purity and unit."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from goldlens.normalize.purity import adjust_for_purity


IDENTITY_COLUMNS = ("Symbol", "Expiry Date", "Date")
REQUIRED_COLUMNS = set(IDENTITY_COLUMNS) | {"settlement_proxy"}


def normalize_per_gram_prices(
    frame: pd.DataFrame,
    contracts: Mapping[str, Mapping[str, Any]],
    target_purity: float = 999,
) -> pd.DataFrame:
    """Return expiry-keyed prices per gram, adjusted to ``target_purity``.

    ``frame`` must contain a settlement proxy and the three identity columns.
    Quote bases and purity figures are read solely from ``contracts``.  Rows
    retain their original symbol, expiry date, and trade date, so no continuous
    or stitched series is created.
    """
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame["settlement_proxy"].isna().any():
        raise ValueError("settlement_proxy contains missing values")

    normalized = frame.copy()
    normalized["Symbol"] = normalized["Symbol"].astype(str).str.strip()
    unknown_symbols = sorted(set(normalized["Symbol"]) - set(contracts))
    if unknown_symbols:
        raise ValueError(f"contracts missing symbols: {unknown_symbols}")

    quote_bases = normalized["Symbol"].map(
        lambda symbol: contracts[symbol]["quote_base_grams"]
    )
    purities = normalized["Symbol"].map(lambda symbol: contracts[symbol]["purity"])
    if (quote_bases <= 0).any():
        raise ValueError("quote_base_grams must be positive")

    normalized["quote_price_per_gram"] = normalized["settlement_proxy"] / quote_bases
    normalized["purity_adjusted_price_per_gram"] = [
        adjust_for_purity(price, purity, target_purity)
        for price, purity in zip(normalized["quote_price_per_gram"], purities, strict=True)
    ]
    normalized["target_purity"] = target_purity
    return normalized
