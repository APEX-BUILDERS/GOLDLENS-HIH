"""Generate contract expiry windows and track unverified calendar events."""

from __future__ import annotations

import calendar as month_calendar
import re
from collections.abc import Mapping
from datetime import date
from typing import Any

import pandas as pd


EXPIRY_WINDOW_PATTERN = re.compile(r"^(?P<start>\d+)(?:st|nd|rd|th)-(?P<end>\d+)(?:st|nd|rd|th)$")
CALENDAR_RULES = ("listing_rule", "tender_start_rule", "tender_end_rule")


def next_expiry_per_contract(
    contracts: Mapping[str, Mapping[str, Any]], as_of: date | pd.Timestamp
) -> pd.DataFrame:
    """Return each contract's next configured expiry *window* on or after ``as_of``.

    The configured source specifies date windows, not a verified exact trading
    day.  This function deliberately returns the window boundaries rather than
    fabricating an exact expiry date.
    """
    reference = pd.Timestamp(as_of).normalize()
    rows = []
    for symbol, specification in sorted(contracts.items()):
        start_day, end_day = _parse_expiry_window(str(specification["expiry_window"]))
        candidate = _window_for_month(reference.year, reference.month, start_day, end_day)
        if candidate["expiry_window_end"] < reference:
            following_month = reference + pd.offsets.MonthBegin(1)
            candidate = _window_for_month(
                following_month.year, following_month.month, start_day, end_day
            )
        rows.append({"symbol": symbol, **candidate, "status": "configured expiry window"})
    return pd.DataFrame(rows)


def contract_calendar_events(
    contracts: Mapping[str, Mapping[str, Any]], as_of: date | pd.Timestamp
) -> pd.DataFrame:
    """Return next expiry windows plus listing/tender events requiring verification."""
    expiry_rows = next_expiry_per_contract(contracts, as_of).assign(event_type="expiry")
    expiry_rows["event_date"] = pd.NaT
    pending_rows = []
    for symbol, specification in sorted(contracts.items()):
        for rule_name in CALENDAR_RULES:
            pending_rows.append(
                {
                    "symbol": symbol,
                    "event_type": rule_name.removesuffix("_rule"),
                    "event_date": pd.NaT,
                    "expiry_window_start": pd.NaT,
                    "expiry_window_end": pd.NaT,
                    "status": str(specification.get(rule_name, "TODO(verify)")),
                }
            )
    return pd.concat([expiry_rows, pd.DataFrame(pending_rows)], ignore_index=True)


def _parse_expiry_window(rule: str) -> tuple[int, int]:
    """Parse the configured inclusive day-of-month range."""
    match = EXPIRY_WINDOW_PATTERN.fullmatch(rule)
    if not match:
        raise ValueError(f"invalid expiry_window: {rule!r}")
    start_day = int(match.group("start"))
    end_day = int(match.group("end"))
    if start_day < 1 or end_day < start_day or end_day > 31:
        raise ValueError(f"invalid expiry_window: {rule!r}")
    return start_day, end_day


def _window_for_month(year: int, month: int, start_day: int, end_day: int) -> dict[str, pd.Timestamp]:
    """Return a day-of-month window, capped at the month's last calendar day."""
    month_end = month_calendar.monthrange(year, month)[1]
    if start_day > month_end:
        raise ValueError("expiry window does not occur in this month")
    return {
        "expiry_window_start": pd.Timestamp(year=year, month=month, day=start_day),
        "expiry_window_end": pd.Timestamp(year=year, month=month, day=min(end_day, month_end)),
    }
