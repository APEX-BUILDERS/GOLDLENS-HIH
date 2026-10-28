"""Command-line entry point for S8 cost application."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from goldlens.backtest.costs import apply_trading_costs, load_cost_scenarios


def run_cost_scenarios(
    database_path: str | Path,
    costs_path: str | Path,
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cost the actual S7 trades under every configured scenario.

    Returns expiry-keyed trade rows and one all-trade summary row per scenario.
    An edge survives only when aggregate net P&L remains positive after costs.
    """
    scenarios = load_cost_scenarios(costs_path)
    with duckdb.connect(str(database_path)) as connection:
        trades = connection.execute("SELECT * FROM backtest_trades").fetchdf()
        if trades.empty:
            raise ValueError("backtest_trades is empty; run the real-data S7 replay first")
        costed_frames: list[pd.DataFrame] = []
        summaries: list[dict[str, object]] = []
        for scenario, rates in scenarios.items():
            costed = apply_trading_costs(trades, rates, min_volume_lots, min_open_interest_lots)
            costed.insert(0, "scenario", scenario)
            exposure = costed["left_entry_notional"] + costed["right_entry_notional"]
            gross_pnl = float(costed["gross_pnl"].sum())
            net_pnl = float(costed["net_pnl"].sum())
            total_exposure = float(exposure.sum())
            summaries.append(
                {
                    "scenario": scenario,
                    "trades": len(costed),
                    "gross_pnl": gross_pnl,
                    "net_pnl": net_pnl,
                    "gross_return": gross_pnl / total_exposure,
                    "net_return": net_pnl / total_exposure,
                    "edge_survives_costs": net_pnl > 0,
                }
            )
            costed_frames.append(costed)
        costed_trades = pd.concat(costed_frames, ignore_index=True)
        summary = pd.DataFrame(summaries).sort_values(
            "scenario", key=lambda column: column.map({"low": 0, "base": 1, "high": 2})
        ).reset_index(drop=True)
        summary["verdict_changes_between_scenarios"] = summary["edge_survives_costs"].nunique() > 1
        connection.register("costed_trade_rows", costed_trades)
        connection.register("cost_scenario_rows", summary)
        connection.execute("CREATE OR REPLACE TABLE backtest_costed_trades AS SELECT * FROM costed_trade_rows")
        connection.execute("CREATE OR REPLACE TABLE backtest_cost_scenarios AS SELECT * FROM cost_scenario_rows")
    return costed_trades, summary


def apply_configured_costs(
    database_path: str | Path,
    costs_path: str | Path,
    min_volume_lots: int,
    min_open_interest_lots: int,
) -> int:
    """Run all configured cost scenarios and return the count of real S7 trades."""
    costed, _ = run_cost_scenarios(
        database_path, costs_path, min_volume_lots, min_open_interest_lots
    )
    return len(costed) // 3


def main() -> None:
    """Apply S8 cost inputs from configuration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/goldlens.duckdb"))
    parser.add_argument("--costs", type=Path, default=Path("config/costs.yml"))
    parser.add_argument("--min-volume-lots", type=int, default=1)
    parser.add_argument("--min-open-interest-lots", type=int, default=1)
    args = parser.parse_args()
    costed, summary = run_cost_scenarios(
        args.db, args.costs, args.min_volume_lots, args.min_open_interest_lots
    )
    print(f"costed real backtest trades written per scenario: {len(costed) // len(summary)}")
    print(summary.to_string(index=False, formatters={
        "gross_pnl": "{:.2f}".format,
        "net_pnl": "{:.2f}".format,
        "gross_return": "{:.6%}".format,
        "net_return": "{:.6%}".format,
    }))
    print(
        "verdict changes between scenarios: "
        f"{bool(summary['verdict_changes_between_scenarios'].iloc[0])}"
    )


if __name__ == "__main__":
    main()
