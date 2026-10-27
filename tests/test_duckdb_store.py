import pandas as pd

from goldlens.store.duckdb_store import write_clean_rows


def test_rows_keyed_by_expiry(tmp_path) -> None:
    rows = pd.DataFrame({
        "Symbol": ["GOLDTEN", "GOLDTEN"],
        "Expiry Date": [pd.Timestamp("2025-04-30"), pd.Timestamp("2025-05-30")],
        "Date": [pd.Timestamp("2025-03-31"), pd.Timestamp("2025-03-31")],
        "Close": [80000.0, 80100.0],
    })
    database = tmp_path / "goldlens.duckdb"
    write_clean_rows(rows, database)

    import duckdb

    with duckdb.connect(str(database)) as connection:
        count = connection.execute("SELECT COUNT(*) FROM clean_futures").fetchone()[0]
    assert count == 2
