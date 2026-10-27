from datetime import date
from pathlib import Path

import pandas as pd

from goldlens.calendar.contract_calendar import contract_calendar_events, next_expiry_per_contract
from goldlens.ingest.contract_registry import load_contracts


def _contracts() -> dict:
    return load_contracts(Path(__file__).parents[1] / "config" / "contracts.yml")


def test_next_expiry_per_contract() -> None:
    upcoming = next_expiry_per_contract(_contracts(), date(2026, 10, 27)).set_index("symbol")

    assert set(upcoming.index) == {"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"}
    assert upcoming.loc["GOLDM", "expiry_window_start"] == pd.Timestamp("2026-11-03")
    assert upcoming.loc["GOLDM", "expiry_window_end"] == pd.Timestamp("2026-11-05")
    assert upcoming.loc["GOLDTEN", "expiry_window_start"] == pd.Timestamp("2026-10-27")
    assert upcoming.loc["GOLDTEN", "expiry_window_end"] == pd.Timestamp("2026-10-31")


def test_listing_and_tender_dates_remain_todo_until_verified() -> None:
    events = contract_calendar_events(_contracts(), date(2026, 10, 27))
    unverified = events[events["event_type"] != "expiry"]

    assert len(unverified) == 12
    assert unverified["event_date"].isna().all()
    assert unverified["status"].eq("TODO(verify)").all()
