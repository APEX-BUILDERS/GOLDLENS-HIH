"""Local Streamlit dashboard for real, materialized GoldLens results."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from goldlens.ingest.pipeline import ingest_reports  # noqa: E402


DATABASE = ROOT / "data" / "goldlens.duckdb"
RAW_DATA = ROOT / "data" / "raw"
PAIR_OPTIONS = [
    ("GOLDTEN", "GOLDPETAL"),
    ("GOLDM", "GOLDTEN"),
    ("GOLDM", "GOLDGUINEA"),
    ("GOLDM", "GOLDPETAL"),
    ("GOLDTEN", "GOLDGUINEA"),
    ("GOLDGUINEA", "GOLDPETAL"),
]


@st.cache_data(show_spinner="Loading local DuckDB data…")
def load_table(table_name: str) -> pd.DataFrame:
    """Load one materialized local table; no network or REST layer is used."""
    if not DATABASE.exists():
        return pd.DataFrame()
    with duckdb.connect(str(DATABASE), read_only=True) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        if table_name not in tables:
            return pd.DataFrame()
        return connection.execute(f'SELECT * FROM "{table_name}"').fetchdf()


@st.cache_data(show_spinner="Checking real raw-data quality…")
def load_data_quality() -> dict[str, object]:
    """Recompute the ingestion quality summary from supplied raw reports only."""
    if not RAW_DATA.exists():
        return {}
    _, summary = ingest_reports(RAW_DATA)
    return asdict(summary)


def _pair_frame(signals: pd.DataFrame, first: str, second: str) -> pd.DataFrame:
    """Orient an unordered selected pair without joining or stitching expiries."""
    direct = signals[(signals["left_symbol"] == first) & (signals["right_symbol"] == second)].copy()
    if not direct.empty:
        return direct
    reverse = signals[(signals["left_symbol"] == second) & (signals["right_symbol"] == first)].copy()
    if reverse.empty:
        return reverse
    reverse["spread_bps"] *= -1
    reverse["rolling_mean_bps"] *= -1
    reverse["zscore"] *= -1
    reverse[["left_symbol", "right_symbol"]] = reverse[["right_symbol", "left_symbol"]].to_numpy()
    reverse[["left_expiry_date", "right_expiry_date"]] = reverse[
        ["right_expiry_date", "left_expiry_date"]
    ].to_numpy()
    return reverse


def _spread_chart(signals: pd.DataFrame, alerts: pd.DataFrame, first: str, second: str) -> go.Figure:
    """Plot exact-expiry spread series and their own prior-only normal bands."""
    selected = _pair_frame(signals, first, second)
    figure = go.Figure()
    if selected.empty:
        figure.add_annotation(text="No real spread rows for this pair", showarrow=False)
        return figure
    selected = selected.copy()
    selected["Date"] = pd.to_datetime(selected["Date"])
    for (left_expiry, right_expiry), series in selected.groupby(
        ["left_expiry_date", "right_expiry_date"], sort=True
    ):
        label = f"{pd.Timestamp(left_expiry):%d %b %Y} / {pd.Timestamp(right_expiry):%d %b %Y}"
        series = series.sort_values("Date")
        upper = series["rolling_mean_bps"] + series["rolling_std_bps"]
        lower = series["rolling_mean_bps"] - series["rolling_std_bps"]
        figure.add_trace(go.Scatter(x=series["Date"], y=upper, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        figure.add_trace(go.Scatter(x=series["Date"], y=lower, mode="lines", line={"width": 0}, fill="tonexty", fillcolor="rgba(100, 116, 139, 0.12)", name=f"normal band: {label}", legendgroup=label, hoverinfo="skip"))
        figure.add_trace(go.Scatter(x=series["Date"], y=series["spread_bps"], mode="lines", name=label, legendgroup=label))
    if not alerts.empty:
        marked = _pair_frame(alerts, first, second)
        if not marked.empty:
            figure.add_trace(go.Scatter(x=marked["alert_date"], y=marked["spread_bps"], mode="markers", marker={"color": "#dc2626", "size": 10, "symbol": "diamond"}, name="quiet alert"))
    figure.update_layout(title=f"{first} − {second}: normalized spread (exact expiry pairs; not stitched)", xaxis_title="Trade date", yaxis_title="Spread (bps)", legend_title="Expiry pair")
    return figure


def _format_pct(value: object) -> str:
    return "—" if pd.isna(value) else f"{float(value):.4%}"


def _backtest_metrics(costed: pd.DataFrame) -> tuple[float | None, float | None]:
    """Return base-case maximum drawdown and turnover from stored real trades."""
    base = costed[costed.get("scenario", pd.Series(dtype=str)) == "base"].copy()
    if base.empty:
        return None, None
    base["exit_date"] = pd.to_datetime(base["exit_date"])
    daily = base.groupby("exit_date", as_index=False)["net_pnl"].sum().sort_values("exit_date")
    cumulative = daily["net_pnl"].cumsum()
    drawdown = cumulative - cumulative.cummax()
    exposure = base["left_entry_notional"] + base["right_entry_notional"]
    turnover = base["round_trip_turnover"].sum() / exposure.sum()
    return float(drawdown.min()), float(turnover)


def main() -> None:
    st.set_page_config(page_title="GoldLens", page_icon="🟨", layout="wide")
    st.title("GoldLens")
    st.caption("Local MCX gold-futures comparison — expiry keyed, real-data only, and not a price-prediction tool.")

    signals = load_table("spread_signals")
    alerts = load_table("quiet_alerts")
    calendar = load_table("contract_calendar")
    scenarios = load_table("backtest_cost_scenarios")
    phases = load_table("backtest_attribution_phase")
    costed = load_table("backtest_costed_trades")

    st.subheader("Spread monitor")
    pair_label = st.selectbox("Contract pair", [f"{left} vs {right}" for left, right in PAIR_OPTIONS], index=0)
    first, second = pair_label.split(" vs ")
    st.plotly_chart(_spread_chart(signals, alerts, first, second), width="stretch")

    left, right = st.columns(2)
    with left:
        st.subheader("Quiet alert state")
        current_alerts = alerts[(alerts["left_symbol"].isin([first, second])) & (alerts["right_symbol"].isin([first, second]))] if not alerts.empty else alerts
        latest = _pair_frame(signals, first, second)
        latest = latest[pd.to_datetime(latest["Date"]) == pd.to_datetime(latest["Date"]).max()] if not latest.empty else latest
        raw_suppressed = max(len(latest) - len(current_alerts), 0)
        is_alert = not current_alerts.empty
        st.metric("State", "alert: beyond band" if is_alert else "quiet")
        base_row = scenarios.loc[scenarios["scenario"] == "base"] if not scenarios.empty else pd.DataFrame()
        clears_costs = bool(base_row["edge_survives_costs"].iloc[0]) if not base_row.empty else False
        st.write(f"- Z-score band: {'beyond band' if is_alert else 'within band or unavailable'}")
        st.write(f"- Liquidity: {'passes for alert' if is_alert else 'not a qualifying liquid alert'}")
        st.write(f"- Clears modeled base costs: {'yes' if clears_costs else 'no'}")
        st.caption(f"Raw latest-date signal rows suppressed for this pair: {raw_suppressed}")
    with right:
        st.subheader("Contract calendar")
        if calendar.empty:
            st.info("Run the S6 calendar materialization to view configured expiry windows and events.")
        else:
            st.dataframe(calendar.sort_values(["symbol", "event_type"]), width="stretch", hide_index=True)

    st.subheader("Backtest after modeled costs")
    base = scenarios.loc[scenarios["scenario"] == "base"] if not scenarios.empty else pd.DataFrame()
    max_drawdown, turnover = _backtest_metrics(costed)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Base net return", _format_pct(base["net_return"].iloc[0]) if not base.empty else "—")
    metric_columns[1].metric("Return ex gold move", "Not calculated (no gold-move proxy)")
    metric_columns[2].metric("Base max drawdown", "—" if max_drawdown is None else f"Rs {max_drawdown:,.0f}")
    metric_columns[3].metric("Base turnover / entry exposure", "—" if turnover is None else f"{turnover:.2f}x")
    if not phases.empty:
        base_phases = phases[phases["scenario"] == "base"].copy()
        base_phases["net_return"] = base_phases["net_return"].map(_format_pct)
        st.caption("Base scenario, separated by non-overlapping signal/entry/exit phase.")
        st.dataframe(base_phases[["phase", "trades", "gross_pnl", "total_cost", "net_pnl", "net_return"]], width="stretch", hide_index=True)
    if not scenarios.empty:
        scenario_display = scenarios.copy()
        scenario_display["gross_return"] = scenario_display["gross_return"].map(_format_pct)
        scenario_display["net_return"] = scenario_display["net_return"].map(_format_pct)
        st.dataframe(scenario_display, width="stretch", hide_index=True)

    st.subheader("Verdict")
    if not base.empty and bool(base["edge_survives_costs"].iloc[0]):
        outcome = "The modeled base-case edge survives costs."
    else:
        outcome = "The modeled base-case edge does not survive costs."
    st.warning(
        f"{outcome} Limits: Close is a declared settlement proxy; execution assumes the next trading day; "
        "possible missing expiries are GOLDM Dec 2025 and GOLDPETAL Nov 2026; all four contracts share 387 trading dates "
        "from 2025-03-31 to 2026-10-23; and low/base/high cost scenarios are assumptions."
    )

    with st.expander("Data quality"):
        quality = load_data_quality()
        if not quality:
            st.info("No raw files are available under data/raw/.")
        else:
            st.write(f"Rows read: {quality['rows_read']:,}; kept: {quality['rows_after_deduplication']:,}; rejected files: {quality['files_rejected']:,}; duplicates removed: {quality['duplicates_removed']:,}.")
            st.write("Expiries per symbol:", quality["expiries_per_symbol"])
            if quality["date_problems"]:
                st.caption("Rejected/quality notes: " + " | ".join(quality["date_problems"]))


if __name__ == "__main__":
    main()
