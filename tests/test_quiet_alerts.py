import pandas as pd

from goldlens.alerts.quiet import build_quiet_alerts


def _signals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-10-22", "2026-10-23", "2026-10-23"]),
            "left_symbol": ["GOLDM", "GOLDM", "GOLDTEN"],
            "left_expiry_date": pd.to_datetime(["2026-11-05"] * 3),
            "right_symbol": ["GOLDTEN", "GOLDTEN", "GOLDM"],
            "right_expiry_date": pd.to_datetime(["2026-11-30"] * 3),
            "spread_bps": [4.0, 5.0, 6.0],
            "zscore": [3.0, -2.5, 3.5],
            "liquid": [True, True, False],
        }
    )


def test_quiet_alerts_are_only_for_latest_liquid_threshold_crossings() -> None:
    alerts = build_quiet_alerts(_signals(), zscore_threshold=2.0)

    assert len(alerts) == 1
    assert alerts.loc[0, "alert_date"] == pd.Timestamp("2026-10-23")
    assert alerts.loc[0, "signal_direction"] == "long_left_short_right"
    assert "not a price prediction" in alerts.loc[0, "message"]


def test_quiet_alerts_reject_non_positive_threshold() -> None:
    try:
        build_quiet_alerts(_signals(), zscore_threshold=0)
    except ValueError as as_error:
        assert str(as_error) == "zscore_threshold must be positive"
    else:
        raise AssertionError("expected a positive threshold validation error")


def test_quiet_alerts_as_of_date_ignores_later_rows() -> None:
    signals = _signals()
    later = signals.iloc[[1]].copy()
    later["Date"] = pd.Timestamp("2026-10-24")
    later["zscore"] = 99.0
    full = pd.concat([signals, later], ignore_index=True)

    alerts = build_quiet_alerts(full, zscore_threshold=2.0, as_of_date="2026-10-23")

    assert len(alerts) == 1
    assert alerts.loc[0, "alert_date"] == pd.Timestamp("2026-10-23")
    assert alerts.loc[0, "zscore"] == -2.5
