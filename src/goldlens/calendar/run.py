"""Command-line entry point for S6 contract calendar events."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from goldlens.calendar.contract_calendar import contract_calendar_events
from goldlens.ingest.contract_registry import load_contracts


def write_contract_calendar(
    database_path: str | Path, contracts_path: str | Path, as_of: date | pd.Timestamp
) -> int:
    """Write configured expiry windows and TODO calendar events to DuckDB."""
    events = contract_calendar_events(load_contracts(contracts_path), as_of)
    with duckdb.connect(str(database_path)) as connection:
        connection.register("contract_calendar_rows", events)
        connection.execute(
            "CREATE OR REPLACE TABLE contract_calendar AS SELECT * FROM contract_calendar_rows"
        )
    return len(events)


def main() -> None:
    """Materialize the configured contract calendar."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--contracts", type=Path, default=Path("config/contracts.yml"))
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    event_count = write_contract_calendar(args.db, args.contracts, args.as_of)
    print(f"calendar events written: {event_count}")


if __name__ == "__main__":
    main()
