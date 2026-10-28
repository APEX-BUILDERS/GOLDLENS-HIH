"""Internal-date ingestion and conflict-safe overlap cleaning for MCX reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


TARGET_SYMBOLS = frozenset({"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"})
PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Previous Close")
REQUIRED_COLUMNS = frozenset({
    "Date", "Instrument Name", "Symbol", "Expiry Date", "Open", "High", "Low",
    "Close", "Previous Close", "Volume(Lots)", "Volume(In 000's)", "Open Interest(Lots)",
})


@dataclass(frozen=True)
class QualitySummary:
    rows_read: int
    rows_kept_before_deduplication: int
    rows_after_deduplication: int
    files_accepted: int
    files_rejected: int
    duplicates_removed: int
    date_problems: tuple[str, ...]
    expiries_per_symbol: dict[str, int]
    expiry_gaps: dict[str, list[str]]
    common_trading_dates: int
    common_date_start: pd.Timestamp | None
    common_date_end: pd.Timestamp | None


def _parse_trade_date(value: object) -> pd.Timestamp:
    """Parse only explicit, unambiguous MCX date formats."""
    for fmt in ("%d %b %Y", "%d-%b-%Y", "%Y-%m-%d"):
        try:
            return pd.Timestamp(pd.to_datetime(str(value).strip(), format=fmt)).normalize()
        except (TypeError, ValueError):
            pass
    raise ValueError(f"unsupported or ambiguous trade date: {value!r}")


def _parse_expiry(value: object) -> pd.Timestamp:
    """Parse compact MCX expiry dates such as 31JAN2025."""
    try:
        return pd.Timestamp(pd.to_datetime(str(value).strip(), format="%d%b%Y")).normalize()
    except (TypeError, ValueError) as error:
        raise ValueError(f"unsupported expiry date: {value!r}") from error


def parse_report(path: str | Path) -> tuple[pd.DataFrame, int]:
    """Read one HTML-in-XLS report and enforce source-internal consistency."""
    report_path = Path(path)
    tables = pd.read_html(report_path)
    if not tables:
        raise ValueError("no HTML table found")
    raw = tables[0].rename(columns={"Volume(In 000’s)": "Volume(In 000's)"})
    missing = REQUIRED_COLUMNS - set(raw.columns)
    if missing:
        raise ValueError(f"missing required columns {sorted(missing)}")
    symbols = raw["Symbol"].astype(str).str.strip().str.upper()
    instruments = raw["Instrument Name"].astype(str).str.strip().str.upper()
    frame = raw.loc[(instruments == "FUTCOM") & symbols.isin(TARGET_SYMBOLS)].copy()
    frame["Symbol"] = symbols.loc[frame.index]
    if frame.empty:
        return frame, len(raw)
    frame["Date"] = frame["Date"].map(_parse_trade_date)
    frame["Expiry Date"] = frame["Expiry Date"].map(_parse_expiry)
    if frame["Expiry Date"].nunique() != 1:
        raise ValueError(f"expected one expiry per file; found {frame['Expiry Date'].nunique()}")
    if (frame["Date"] > frame["Expiry Date"]).any():
        raise ValueError("trade date occurs after expiry date")
    weekend_rows = frame["Date"].dt.day_of_week >= 5
    # Weekend rows are invalid under the project contract. Remove and report
    # them while retaining the independently valid rows in the same report.
    frame = frame.loc[~weekend_rows].copy()
    if frame["Date"].nunique() * 4 < len(frame):
        raise ValueError(
            f"suspect date density: {len(frame)} rows but only {frame['Date'].nunique()} distinct dates"
        )
    for column in PRICE_COLUMNS + ("Volume(Lots)", "Open Interest(Lots)"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    # Retain Volume(In 000's) exactly as supplied: reports may append a unit
    # such as GRMS, so it must not be coerced or assumed to be lots.
    frame["settlement_proxy"] = frame["Close"]
    frame["source_file"] = str(report_path)
    frame.attrs["weekend_rows_removed"] = int(weekend_rows.sum())
    return frame, len(raw)


def deduplicate_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove identical overlap copies and reject any duplicate price conflicts."""
    if frame.empty:
        return frame, 0
    keys = ["Symbol", "Expiry Date", "Date"]
    conflicts = frame.groupby(keys)[list(PRICE_COLUMNS)].nunique(dropna=False)
    bad = conflicts[(conflicts > 1).any(axis=1)]
    if not bad.empty:
        raise ValueError(f"conflicting duplicate prices for {bad.index[0]}")
    cleaned = frame.drop_duplicates(subset=keys, keep="first").copy()
    return cleaned, len(frame) - len(cleaned)


def _expiry_gaps(frame: pd.DataFrame) -> dict[str, list[str]]:
    gaps: dict[str, list[str]] = {}
    for symbol, group in frame.groupby("Symbol"):
        observed = pd.PeriodIndex(group["Expiry Date"].drop_duplicates(), freq="M")
        expected = pd.period_range(observed.min(), observed.max(), freq="M")
        gaps[str(symbol)] = [str(item) for item in expected.difference(observed)]
    return gaps


def ingest_reports(raw_dir: str | Path) -> tuple[pd.DataFrame, QualitySummary]:
    """Parse all HTML-in-XLS sources using internal data only, then clean overlap."""
    root = Path(raw_dir)
    frames: list[pd.DataFrame] = []
    read_rows = 0
    rejected: list[str] = []
    date_problems: list[str] = []
    accepted = 0
    for path in sorted(root.rglob("*.xls")):
        try:
            frame, source_rows = parse_report(path)
        except (ValueError, OSError) as error:
            rejected.append(f"{path.relative_to(root)}: {error}")
            continue
        read_rows += source_rows
        accepted += 1
        if frame.attrs.get("weekend_rows_removed", 0):
            date_problems.append(
                f"{path.relative_to(root)}: removed {frame.attrs['weekend_rows_removed']} weekend rows"
            )
        if not frame.empty:
            frames.append(frame)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    cleaned, duplicates_removed = deduplicate_rows(combined)
    date_sets = [set(group["Date"]) for _, group in cleaned.groupby("Symbol")] if not cleaned.empty else []
    common = set.intersection(*date_sets) if len(date_sets) == 4 else set()
    summary = QualitySummary(
        rows_read=read_rows,
        rows_kept_before_deduplication=len(combined),
        rows_after_deduplication=len(cleaned),
        files_accepted=accepted,
        files_rejected=len(rejected),
        duplicates_removed=duplicates_removed,
        date_problems=tuple(rejected + date_problems),
        expiries_per_symbol={str(symbol): int(group["Expiry Date"].nunique()) for symbol, group in cleaned.groupby("Symbol")},
        expiry_gaps=_expiry_gaps(cleaned) if not cleaned.empty else {},
        common_trading_dates=len(common),
        common_date_start=min(common) if common else None,
        common_date_end=max(common) if common else None,
    )
    return cleaned, summary
