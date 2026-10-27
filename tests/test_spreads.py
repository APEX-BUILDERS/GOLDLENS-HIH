import pandas as pd

from goldlens.analytics.liquidity import apply_liquidity_filter
from goldlens.analytics.spreads import build_expiry_month_spreads
from goldlens.analytics.zscore import add_past_only_rolling_zscore


def _normalized_prices() -> pd.DataFrame:
    dates = pd.date_range("2025-03-24", periods=5, freq="B")
    rows = []
    for index, date in enumerate(dates):
        for symbol, expiry, price in [
            ("GOLDM", "2025-04-04", 100.0 + index),
            ("GOLDTEN", "2025-04-30", 101.0 + index),
            ("GOLDGUINEA", "2025-04-30", 102.0 + index),
            ("GOLDPETAL", "2025-04-30", 103.0 + index),
        ]:
            rows.append(
                {
                    "Symbol": symbol,
                    "Date": date,
                    "Expiry Date": pd.Timestamp(expiry),
                    "quote_price_per_gram": price,
                    "purity_adjusted_price_per_gram": price,
                    "Volume(Lots)": 10 if symbol != "GOLDM" or index != 0 else 0,
                    "Open Interest(Lots)": 20,
                }
            )
    return pd.DataFrame(rows)


def test_all_six_pairs_keep_actual_expiry_dates() -> None:
    spreads = build_expiry_month_spreads(_normalized_prices())

    assert len(spreads[["left_symbol", "right_symbol"]].drop_duplicates()) == 6
    goldm_pair = spreads[(spreads["left_symbol"] == "GOLDM") & (spreads["right_symbol"] == "GOLDTEN")]
    assert set(goldm_pair["left_expiry_date"]) == {pd.Timestamp("2025-04-04")}
    assert set(goldm_pair["right_expiry_date"]) == {pd.Timestamp("2025-04-30")}


def test_liquidity_filter_requires_both_legs() -> None:
    filtered = apply_liquidity_filter(build_expiry_month_spreads(_normalized_prices()), 1, 1)

    goldm_pair = filtered[(filtered["left_symbol"] == "GOLDM") & (filtered["right_symbol"] == "GOLDTEN")]
    assert goldm_pair.iloc[0]["liquid"] == False
    assert goldm_pair.iloc[1:]["liquid"].all()


def test_zscore_ignores_future_rows() -> None:
    spreads = build_expiry_month_spreads(_normalized_prices())
    signals = add_past_only_rolling_zscore(spreads, window=3, min_periods=2)
    target = signals.iloc[3]
    without_future = signals[signals["Date"] <= target["Date"]]
    recomputed = add_past_only_rolling_zscore(without_future, window=3, min_periods=2)
    comparable = recomputed[
        (recomputed["left_symbol"] == target["left_symbol"])
        & (recomputed["right_symbol"] == target["right_symbol"])
        & (recomputed["left_expiry_date"] == target["left_expiry_date"])
        & (recomputed["right_expiry_date"] == target["right_expiry_date"])
        & (recomputed["Date"] == target["Date"])
    ].iloc[0]

    assert comparable["zscore"] == target["zscore"]
