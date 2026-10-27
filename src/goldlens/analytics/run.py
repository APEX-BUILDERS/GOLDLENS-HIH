"""Command-line entry point for S4 spread signals."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.analytics.liquidity import apply_liquidity_filter
from goldlens.analytics.spreads import build_expiry_month_spreads
from goldlens.analytics.zscore import add_past_only_rolling_zscore


def create_spread_signals(
    database_path: str | Path,
    window: int,
    min_periods: int,
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> int:
    """Create real-data spread signals and store them in DuckDB."""
    with duckdb.connect(str(database_path)) as connection:
        normalized = connection.execute("SELECT * FROM normalized_futures").fetchdf()
        spreads = build_expiry_month_spreads(normalized)
        liquid_spreads = apply_liquidity_filter(spreads, min_volume_lots, min_open_interest_lots)
        signals = add_past_only_rolling_zscore(liquid_spreads, window, min_periods)
        connection.register("spread_signal_rows", signals)
        connection.execute(
            "CREATE OR REPLACE TABLE spread_signals AS SELECT * FROM spread_signal_rows"
        )
    return len(signals)


def main() -> None:
    """Calculate stored S4 spread signals from normalized real data."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--min-periods", type=int, default=10)
    parser.add_argument("--min-volume-lots", type=int, default=1)
    parser.add_argument("--min-open-interest-lots", type=int, default=1)
    args = parser.parse_args()
    rows_written = create_spread_signals(
        args.db, args.window, args.min_periods, args.min_volume_lots, args.min_open_interest_lots
    )
    print(f"spread signal rows written: {rows_written}")


if __name__ == "__main__":
    main()
