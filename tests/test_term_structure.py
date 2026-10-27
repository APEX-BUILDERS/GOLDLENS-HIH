import pandas as pd
import pytest

from goldlens.analytics.spreads import build_expiry_month_spreads
from goldlens.analytics.term_structure import add_spread_decomposition, build_term_structure


def _curve_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Symbol": ["GOLDM", "GOLDM", "GOLDTEN", "GOLDTEN"],
            "Date": pd.to_datetime(["2025-03-31"] * 4),
            "Expiry Date": pd.to_datetime(["2025-04-04", "2025-05-04", "2025-04-30", "2025-05-30"]),
            "quote_price_per_gram": [100.0, 102.3076923076923, 102.0, 104.0],
            "purity_adjusted_price_per_gram": [101.0, 103.3076923076923, 102.0, 104.0],
            "Volume(Lots)": [10, 10, 10, 10],
            "Open Interest(Lots)": [20, 20, 20, 20],
        }
    )


def test_spread_decomposition_sums() -> None:
    prices = _curve_prices()
    decomposition = add_spread_decomposition(
        build_expiry_month_spreads(prices), build_term_structure(prices)
    )
    goldm_vs_goldten = decomposition[
        (decomposition["left_symbol"] == "GOLDM")
        & (decomposition["right_symbol"] == "GOLDTEN")
    ].iloc[0]

    assert goldm_vs_goldten["raw_spread_per_gram"] == pytest.approx(
        goldm_vs_goldten["purity_component_per_gram"]
        + goldm_vs_goldten["carry_roll_down_component_per_gram"]
        + goldm_vs_goldten["residual_component_per_gram"]
    )
    assert goldm_vs_goldten["carry_roll_down_component_per_gram"] == pytest.approx(-2.0)


def test_term_structure_keeps_each_expiry() -> None:
    structure = build_term_structure(_curve_prices())

    assert len(structure) == 4
    assert structure[["Symbol", "Date", "Expiry Date"]].duplicated().sum() == 0
    assert set(structure["days_to_expiry"]) == {4, 30, 34, 60}
