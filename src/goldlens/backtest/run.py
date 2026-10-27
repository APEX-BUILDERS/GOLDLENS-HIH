"""Command-line entry point for S7 walk-forward backtesting."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from goldlens.backtest.walk_forward import summarize_backtest, walk_forward_backtest
from goldlens.ingest.contract_registry import load_contracts


def run_backtest(
    database_path: str | Path,
    contracts_path: str | Path,
    window: int,
    min_periods: int,
    zscore_threshold: float,
    target_notional: float,
    train_end: str,
) -> tuple[int, int]:
    """Run a real-data walk-forward backtest and store trades and phase summary."""
    with duckdb.connect(str(database_path)) as connection:
        spreads = connection.execute("SELECT * FROM spread_signals").fetchdf()
        trades = walk_forward_backtest(
            spreads,
            load_contracts(contracts_path),
            window,
            min_periods,
            zscore_threshold,
            target_notional,
            pd.Timestamp(train_end),
        )
        summary = summarize_backtest(trades)
        connection.register("backtest_trade_rows", trades)
        connection.register("backtest_summary_rows", summary)
        connection.execute("CREATE OR REPLACE TABLE backtest_trades AS SELECT * FROM backtest_trade_rows")
        connection.execute("CREATE OR REPLACE TABLE backtest_summary AS SELECT * FROM backtest_summary_rows")
    return len(trades), len(summary)


def main() -> None:
    """Execute the configured S7 replay."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--contracts", type=Path, default=Path("config/contracts.yml"))
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--min-periods", type=int, default=10)
    parser.add_argument("--zscore-threshold", type=float, default=2.0)
    parser.add_argument("--target-notional", type=float, default=20_000_000.0)
    parser.add_argument("--train-end", default="2026-03-31")
    args = parser.parse_args()
    trades, phases = run_backtest(
        args.db,
        args.contracts,
        args.window,
        args.min_periods,
        args.zscore_threshold,
        args.target_notional,
        args.train_end,
    )
    print(f"backtest trades written: {trades}")
    print(f"backtest phases written: {phases}")


if __name__ == "__main__":
    main()
