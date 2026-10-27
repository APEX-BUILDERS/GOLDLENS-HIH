"""Write the S2 clean table to DuckDB."""

from pathlib import Path

import duckdb
import pandas as pd


def write_clean_rows(frame: pd.DataFrame, database_path: str | Path) -> None:
    """Store cleaned rows keyed by symbol, expiry date, and trade date."""
    database = Path(database_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database)) as connection:
        connection.register("incoming_rows", frame)
        connection.execute("CREATE OR REPLACE TABLE clean_futures AS SELECT * FROM incoming_rows")
        connection.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS expiry_key ON clean_futures ("Symbol", "Expiry Date", "Date")'
        )
