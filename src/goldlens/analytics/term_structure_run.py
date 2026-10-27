"""Command-line entry point for S5 term structure and decomposition."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.analytics.spreads import build_expiry_month_spreads
from goldlens.analytics.term_structure import add_spread_decomposition, build_term_structure


def create_term_structure_and_decomposition(database_path: str | Path) -> tuple[int, int]:
    """Store real expiry-keyed term-structure and decomposition tables."""
    with duckdb.connect(str(database_path)) as connection:
        normalized = connection.execute("SELECT * FROM normalized_futures").fetchdf()
        structure = build_term_structure(normalized)
        decomposition = add_spread_decomposition(build_expiry_month_spreads(normalized), structure)
        connection.register("term_structure_rows", structure)
        connection.register("spread_decomposition_rows", decomposition)
        connection.execute("CREATE OR REPLACE TABLE term_structure AS SELECT * FROM term_structure_rows")
        connection.execute(
            "CREATE OR REPLACE TABLE spread_decomposition AS SELECT * FROM spread_decomposition_rows"
        )
    return len(structure), len(decomposition)


def main() -> None:
    """Calculate and store real-data S5 outputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    args = parser.parse_args()
    term_rows, decomposition_rows = create_term_structure_and_decomposition(args.db)
    print(f"term structure rows written: {term_rows}")
    print(f"spread decomposition rows written: {decomposition_rows}")


if __name__ == "__main__":
    main()
