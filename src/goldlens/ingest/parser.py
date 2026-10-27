"""Parser for daily and cumulative MCX commodity-wise Bhavcopy reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from goldlens.ingest.date_utils import DateValidationError, parse_bhavcopy_date, validate_report_dates


TARGET_SYMBOLS = frozenset({"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"})
REQUIRED_COLUMNS = frozenset({"Date", "Instrument Name", "Symbol", "Expiry Date", "Close"})


@dataclass(frozen=True)
class ParseSummary:
    """Auditable row counts and settlement-price metadata for one report."""

    path: Path
    rows_read: int
    rows_kept: int
    rows_rejected: int
    request_date: pd.Timestamp
    settlement_column: str | None
    settlement_proxy_column: str


def _read_report(path: Path) -> pd.DataFrame:
    """Read a CSV or HTML-table report, including HTML served as `.xls`."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    tables = pd.read_html(path)
    if not tables:
        raise ValueError(f"No table found in {path}")
    return tables[0]


def _settlement_column(columns: pd.Index) -> str | None:
    """Identify an explicitly labeled official settlement-price column only."""
    normalized = {str(column).strip().lower(): str(column) for column in columns}
    for candidate in ("settlement price", "settle price", "settlement", "settle"):
        if candidate in normalized:
            return normalized[candidate]
    return None


def parse_bhavcopy_file(
    path: str | Path, requested_date: pd.Timestamp | None = None
) -> tuple[pd.DataFrame, ParseSummary]:
    """Read one validated report and keep only target MCX futures rows.

    No trade dates are inferred from filenames. The filename's requested date
    is validated against dates actually present in the source report.
    """
    report_path = Path(path)
    raw = _read_report(report_path)
    missing = REQUIRED_COLUMNS - set(raw.columns)
    if missing:
        raise ValueError(f"{report_path}: missing required columns {sorted(missing)}")
    request_date = validate_report_dates(report_path, raw["Date"], requested_date)
    symbols = raw["Symbol"].astype(str).str.strip().str.upper()
    instruments = raw["Instrument Name"].astype(str).str.strip().str.upper()
    kept = raw.loc[(instruments == "FUTCOM") & symbols.isin(TARGET_SYMBOLS)].copy()
    kept["Symbol"] = symbols.loc[kept.index]
    kept["Date"] = kept["Date"].map(parse_bhavcopy_date)
    kept["Expiry Date"] = kept["Expiry Date"].map(
        lambda value: pd.to_datetime(value, format="%d%b%Y", errors="raise").normalize()
    )
    # MCX's supplied reports do not label an official settlement field. This
    # explicitly named proxy is never presented as an official settlement.
    kept["settlement_proxy"] = pd.to_numeric(kept["Close"], errors="raise")
    kept["source_file"] = str(report_path)
    summary = ParseSummary(
        path=report_path,
        rows_read=len(raw),
        rows_kept=len(kept),
        rows_rejected=len(raw) - len(kept),
        request_date=request_date,
        settlement_column=_settlement_column(raw.columns),
        settlement_proxy_column="Close",
    )
    return kept, summary


