from pathlib import Path

import duckdb
import pandas as pd
import pytest

from goldlens.ingest.contract_registry import load_contracts
from goldlens.normalize.per_gram import normalize_per_gram_prices
from goldlens.normalize.run import normalize_database


def test_worked_example_per_gram() -> None:
    contracts = load_contracts(Path(__file__).parents[1] / "config" / "contracts.yml")
    prices = pd.DataFrame(
        {
            "Symbol": ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"],
            "Expiry Date": pd.to_datetime(["2025-04-04", "2025-04-30", "2025-04-30", "2025-04-30"]),
            "Date": pd.to_datetime(["2025-03-31"] * 4),
            "settlement_proxy": [100000.0, 100400.0, 80320.0, 10040.0],
        }
    )

    normalized = normalize_per_gram_prices(prices, contracts)

    assert normalized["quote_price_per_gram"].tolist() == [10000.0, 10040.0, 10040.0, 10040.0]
    assert normalized["purity_adjusted_price_per_gram"].tolist() == pytest.approx(
        [10040.201005025125, 10040.0, 10040.0, 10040.0]
    )
    assert normalized[["Symbol", "Expiry Date", "Date"]].equals(prices[["Symbol", "Expiry Date", "Date"]])


def test_normalize_database_writes_expiry_keyed_real_schema(tmp_path) -> None:
    database = tmp_path / "goldlens.duckdb"
    clean_rows = pd.DataFrame(
        {
            "Symbol": ["GOLDTEN", "GOLDTEN"],
            "Expiry Date": pd.to_datetime(["2025-04-30", "2025-05-30"]),
            "Date": pd.to_datetime(["2025-03-31", "2025-03-31"]),
            "settlement_proxy": [100400.0, 100500.0],
        }
    )
    with duckdb.connect(str(database)) as connection:
        connection.register("clean_rows", clean_rows)
        connection.execute("CREATE TABLE clean_futures AS SELECT * FROM clean_rows")

    count = normalize_database(database, Path(__file__).parents[1] / "config" / "contracts.yml")

    with duckdb.connect(str(database)) as connection:
        result = connection.execute(
            'SELECT "Symbol", "Expiry Date", "Date", purity_adjusted_price_per_gram '
            'FROM normalized_futures ORDER BY "Expiry Date"'
        ).fetchdf()
    assert count == 2
    assert len(result) == 2
    assert result["purity_adjusted_price_per_gram"].tolist() == [10040.0, 10050.0]


def test_normalization_rejects_unknown_symbols() -> None:
    prices = pd.DataFrame(
        {
            "Symbol": ["UNKNOWN"],
            "Expiry Date": pd.to_datetime(["2025-04-30"]),
            "Date": pd.to_datetime(["2025-03-31"]),
            "settlement_proxy": [100.0],
        }
    )

    with pytest.raises(ValueError, match="contracts missing symbols"):
        normalize_per_gram_prices(prices, {})
