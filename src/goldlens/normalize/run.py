"""Command-line entry point for S3 price normalization."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.ingest.contract_registry import load_contracts
from goldlens.normalize.per_gram import normalize_per_gram_prices


def normalize_database(database_path: str | Path, contracts_path: str | Path) -> int:
    """Normalize stored clean futures and write the expiry-keyed result to DuckDB."""
    with duckdb.connect(str(database_path)) as connection:
        clean_rows = connection.execute("SELECT * FROM clean_futures").fetchdf()
        normalized = normalize_per_gram_prices(clean_rows, load_contracts(contracts_path))
        connection.register("normalized_rows", normalized)
        connection.execute(
            "CREATE OR REPLACE TABLE normalized_futures AS SELECT * FROM normalized_rows"
        )
        connection.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS normalized_expiry_key '
            'ON normalized_futures ("Symbol", "Expiry Date", "Date")'
        )
    return len(normalized)


def main() -> None:
    """Normalize clean rows from the configured DuckDB database."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--contracts", type=Path, default=Path("config/contracts.yml"))
    args = parser.parse_args()
    rows_written = normalize_database(args.db, args.contracts)
    print(f"normalized rows written: {rows_written}")


if __name__ == "__main__":
    main()
