"""Command-line entry point for S8 cost application."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from goldlens.backtest.costs import apply_trading_costs, load_cost_rates


def apply_configured_costs(
    database_path: str | Path,
    costs_path: str | Path,
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> int:
    """Apply verified config costs to the actual S7 trades and store net results."""
    rates = load_cost_rates(costs_path)
    with duckdb.connect(str(database_path)) as connection:
        trades = connection.execute("SELECT * FROM backtest_trades").fetchdf()
        costed = apply_trading_costs(trades, rates, min_volume_lots, min_open_interest_lots)
        connection.register("costed_trade_rows", costed)
        connection.execute("CREATE OR REPLACE TABLE backtest_costed_trades AS SELECT * FROM costed_trade_rows")
    return len(costed)


def main() -> None:
    """Apply S8 cost inputs from configuration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--costs", type=Path, default=Path("config/costs.yml"))
    parser.add_argument("--min-volume-lots", type=int, default=1)
    parser.add_argument("--min-open-interest-lots", type=int, default=1)
    args = parser.parse_args()
    count = apply_configured_costs(
        args.db, args.costs, args.min_volume_lots, args.min_open_interest_lots
    )
    print(f"costed backtest trades written: {count}")


if __name__ == "__main__":
    main()
