"""Command-line entry point for local-only quiet research alerts."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.alerts.quiet import build_quiet_alerts


def materialize_quiet_alerts(
    database_path: str | Path,
    zscore_threshold: float = 2.0,
    as_of_date: str | None = None,
) -> int:
    """Write current-date local watches; this function sends no notification."""
    with duckdb.connect(str(database_path)) as connection:
        signals = connection.execute("SELECT * FROM spread_signals").fetchdf()
        alerts = build_quiet_alerts(signals, zscore_threshold, as_of_date)
        connection.register("quiet_alert_rows", alerts)
        connection.execute("CREATE OR REPLACE TABLE quiet_alerts AS SELECT * FROM quiet_alert_rows")
    return len(alerts)


def main() -> None:
    """Materialize current local watches from real materialized signals."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--zscore-threshold", type=float, default=2.0)
    parser.add_argument("--as-of", default=None, help="Observed signal date to materialize; defaults to the latest.")
    args = parser.parse_args()
    count = materialize_quiet_alerts(args.db, args.zscore_threshold, args.as_of)
    print(f"quiet research watches written: {count}; no notification was sent")


if __name__ == "__main__":
    main()
