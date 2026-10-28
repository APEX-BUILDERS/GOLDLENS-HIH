"""Materialize S9 attribution tables from real S8 costed trades."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.backtest.attribution import build_attribution_tables


def run_attribution(database_path: str | Path) -> dict[str, int]:
    """Store scenario, phase, and expiry-pair attribution from real S8 rows."""
    with duckdb.connect(str(database_path)) as connection:
        trades = connection.execute("SELECT * FROM backtest_costed_trades").fetchdf()
        if trades.empty:
            raise ValueError("backtest_costed_trades is empty; run the real-data S8 cost report first")
        tables = build_attribution_tables(trades)
        for name, table in tables.items():
            relation = f"attribution_{name}_rows"
            connection.register(relation, table)
            connection.execute(
                f"CREATE OR REPLACE TABLE backtest_attribution_{name} AS SELECT * FROM {relation}"
            )
    return {name: len(table) for name, table in tables.items()}


def main() -> None:
    """Materialize the S9 real-data cost attribution tables."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    args = parser.parse_args()
    counts = run_attribution(args.db)
    print("attribution rows written: " + ", ".join(f"{name}={count}" for name, count in counts.items()))


if __name__ == "__main__":
    main()
