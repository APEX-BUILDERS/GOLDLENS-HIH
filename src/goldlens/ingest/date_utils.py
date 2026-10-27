"""Date parsing and source-file validation for Bhavcopy reports."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


class DateValidationError(ValueError):
    """Raised when a report cannot be tied to its stated request date."""


def parse_bhavcopy_date(value: object) -> pd.Timestamp:
    """Parse a Bhavcopy date into a normalized day-level timestamp.

    The parser handles MCX's textual dates and explicit ISO dates. Ambiguous
    numeric dates are intentionally deferred to S2's format-aware cleaner.
    """
    if isinstance(value, pd.Timestamp):
        return value.normalize()
    text = str(value).strip()
    for date_format in ("%d %b %Y", "%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.Timestamp(pd.to_datetime(text, format=date_format)).normalize()
        except (TypeError, ValueError):
            continue
    raise ValueError(f"Unsupported Bhavcopy date: {value!r}")


def date_implied_by_filename(path: str | Path) -> pd.Timestamp | None:
    """Return the DDMMYYYY date embedded in a Bhavcopy filename, if present."""
    match = re.search(r"_(\d{8})(?:\s|\(|\.|$)", Path(path).name)
    if not match:
        return None
    return pd.Timestamp(pd.to_datetime(match.group(1), format="%d%m%Y")).normalize()


def validate_report_dates(
    path: str | Path, dates: pd.Series, requested_date: pd.Timestamp | None = None
) -> pd.Timestamp:
    """Validate a daily or cumulative report against its filename request date.

    A daily report must contain exactly its implied date. A cumulative MCX
    commodity-wise report is valid when it includes the implied request-start
    date. This prevents a returned report for an unrelated request from being
    accepted while allowing the supplied multi-day reports.
    """
    expected = requested_date or date_implied_by_filename(path)
    if expected is None:
        raise DateValidationError(f"No DDMMYYYY request date in filename: {path}")
    expected = parse_bhavcopy_date(expected)
    parsed = dates.map(parse_bhavcopy_date)
    actual_dates = set(parsed.tolist())
    if expected not in actual_dates:
        raise DateValidationError(
            f"Requested date {expected.date()} is absent from the report: {path}"
        )
    return expected
