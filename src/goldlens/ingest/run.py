"""Command-line entry point for S1 report validation and parsing."""

from __future__ import annotations

import argparse
from pathlib import Path

from goldlens.ingest.pipeline import ingest_reports
from goldlens.store.duckdb_store import write_clean_rows


def main() -> None:
    """Run S1 validation, S2 overlap cleaning, and DuckDB storage."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    args = parser.parse_args()
    frame, summary = ingest_reports(args.raw)
    write_clean_rows(frame, args.db)
    print(f"rows read: {summary.rows_read}")
    print(f"rows kept before deduplication: {summary.rows_kept_before_deduplication}")
    print(f"rows kept: {summary.rows_after_deduplication}")
    print(f"files accepted: {summary.files_accepted}")
    print(f"files rejected: {summary.files_rejected}")
    print(f"duplicates removed: {summary.duplicates_removed}")
    print(f"date problems: {len(summary.date_problems)}")
    print("settlement proxy: Close (stored as settlement_proxy; not official settlement)")
    print(f"expiries per symbol: {summary.expiries_per_symbol}")
    print(f"expiry gaps: {summary.expiry_gaps}")
    print(f"common trading dates: {summary.common_trading_dates}")
    print(f"common trading range: {summary.common_date_start} to {summary.common_date_end}")
    for reason in summary.date_problems:
        print(f"DATE PROBLEM: {reason}")


if __name__ == "__main__":
    main()
