"""Local Streamlit dashboard for real, materialized GoldLens results."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from goldlens.ingest.pipeline import ingest_reports  # noqa: E402
from ui.assets import image_data_uri, load_asset
from ui.components import kpi, spec, step
from ui.hero_art import stacked_bars_svg
from ui.theme import PLOTLY_LAYOUT, apply_theme


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
    figure.update_layout(**PLOTLY_LAYOUT)
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


def _latest_prices(normalized: pd.DataFrame) -> dict[str, str]:
    """Format the newest existing normalized quotes without changing source data."""
    if normalized.empty:
        return {}
    frame = normalized.copy()
    frame["Date"] = pd.to_datetime(frame["Date"])
    frame = frame[frame["Date"] == frame["Date"].max()]
    latest = frame.groupby("Symbol", as_index=False)["purity_adjusted_price_per_gram"].median()
    return {row.Symbol: f"Rs {row.purity_adjusted_price_per_gram:,.0f}/g" for row in latest.itertuples()}


def _term_structure_chart(term_structure: pd.DataFrame) -> go.Figure:
    """Show one latest-date curve per contract from the existing materialization."""
    figure = go.Figure()
    if term_structure.empty:
        figure.add_annotation(text="No materialized term-structure rows", showarrow=False)
        return figure
    frame = term_structure.copy()
    frame["Date"] = pd.to_datetime(frame["Date"])
    latest = frame[frame["Date"] == frame["Date"].max()]
    for symbol, series in latest.groupby("Symbol", sort=True):
        series = series.sort_values("days_to_expiry")
        figure.add_trace(go.Scatter(x=series["days_to_expiry"], y=series["purity_adjusted_price_per_gram"], mode="lines+markers", name=symbol))
    figure.update_layout(**PLOTLY_LAYOUT)
    figure.update_layout(title="Latest materialized term structure", xaxis_title="Days to expiry", yaxis_title="Purity-adjusted price (Rs/g)")
    return figure


def _contracts() -> dict[str, dict[str, object]]:
    """Read display-only contract specifications from the established config file."""
    with (ROOT / "config" / "contracts.yml").open(encoding="utf-8") as source:
        return yaml.safe_load(source)["contracts"]


def _verdict(base: pd.DataFrame) -> str:
    return "The modeled base-case edge survives costs." if not base.empty and bool(base["edge_survives_costs"].iloc[0]) else "The modeled base-case edge does not survive costs."


def _header(verdict: str) -> None:
    verdict_class = "status-positive" if "survives" in verdict else "status-negative"
    logo = image_data_uri(load_asset("logo.png"))
    logo_markup = (
        f'<img class="header-logo" src="{logo}" alt="GoldLens — expiry-keyed MCX gold futures comparison" />'
        if logo
        else '<div class="fallback-wordmark"><span>Gold</span>Lens</div>'
    )
    st.markdown(
        f'''<div class="utility-bar"><span>The Backend Bench | HackInHills Round 2 | PS 03</span><span>Data: MCX Bhavcopy, 2025-03-31 to 2026-10-23</span></div>
        <div class="brand-header"><div>{logo_markup}<div class="tagline">A disciplined lens for expiry-keyed MCX gold-futures comparisons.</div></div><div class="info-strip"><div><div class="info-label">Data window</div><div class="info-value">387 shared dates</div></div><div><div class="info-label">Contracts tracked</div><div class="info-value">4 contracts</div></div><div><div class="info-label">Verdict status</div><div class="info-value {verdict_class}">{verdict}</div></div></div></div>''',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="GoldLens", page_icon=load_asset("favicon.png") or "🟨", layout="wide")
    apply_theme()
    st.title("GoldLens")

    signals = load_table("spread_signals")
    alerts = load_table("quiet_alerts")
    calendar = load_table("contract_calendar")
    scenarios = load_table("backtest_cost_scenarios")
    phases = load_table("backtest_attribution_phase")
    costed = load_table("backtest_costed_trades")
    base = scenarios.loc[scenarios["scenario"] == "base"] if not scenarios.empty else pd.DataFrame()
    max_drawdown, turnover = _backtest_metrics(costed)
    normalized = load_table("normalized_futures")
    term_structure = load_table("term_structure")
    verdict = _verdict(base)
    _header(verdict)
    prices = _latest_prices(normalized)

    overview, spreads, term, backtest, calendar_tab, quality_tab = st.tabs(["Overview", "Spreads", "Term Structure", "Backtest", "Calendar", "Data Quality"])
    with overview:
        chips = "".join(f'<div class="chip">{symbol} <span>{prices.get(symbol, "")}</span></div>' for symbol in ("GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"))
        st.markdown(f'<div class="hero"><div class="hero-copy"><div class="hero-wordmark">GoldLens</div><h1>Are MCX gold spreads real or noise?</h1><p>Compare like-for-like futures after quote-base, purity, expiry, liquidity, and trading-cost adjustments.</p><div class="chips">{chips}</div></div><div class="hero-art">{stacked_bars_svg()}</div></div>', unsafe_allow_html=True)
        cols = st.columns(3)
        with cols[0]: kpi("Net return after costs", _format_pct(base["net_return"].iloc[0]) if not base.empty else "—", "Base scenario")
        with cols[1]: kpi("Return ex gold move", "Not calculated", "No gold-move proxy")
        with cols[2]: kpi("Verdict", "Does not survive" if "does not" in verdict else "Survives", "Modeled base costs")
        st.markdown("<div class='section-title' style='margin-top:1.7rem'>How it works</div><p class='section-note'>A transparent research workflow, with no price prediction or execution instruction.</p>", unsafe_allow_html=True)
        steps = st.columns(4)
        with steps[0]: step(1, "Ingest", "Read supplied MCX bhavcopy reports.")
        with steps[1]: step(2, "Normalize", "Align quote bases, purity, and expiry.")
        with steps[2]: step(3, "Backtest with costs", "Use past-only signals and next-day execution.")
        with steps[3]: step(4, "Verdict", "Test whether the modeled edge survives costs.")

    with spreads:
        st.markdown("<div class='section-title'>Spread monitor</div><p class='section-note'>Every trace remains an exact-expiry pair; no near-month stitching.</p>", unsafe_allow_html=True)
        pair_label = st.selectbox("Contract pair", [f"{left} vs {right}" for left, right in PAIR_OPTIONS], index=0)
        first, second = pair_label.split(" vs ")
        st.plotly_chart(_spread_chart(signals, alerts, first, second), width="stretch")
        left, right = st.columns(2)
        current_alerts = alerts[(alerts["left_symbol"].isin([first, second])) & (alerts["right_symbol"].isin([first, second]))] if not alerts.empty else alerts
        latest = _pair_frame(signals, first, second)
        latest = latest[pd.to_datetime(latest["Date"]) == pd.to_datetime(latest["Date"]).max()] if not latest.empty else latest
        raw_suppressed = max(len(latest) - len(current_alerts), 0)
        is_alert = not current_alerts.empty
        with left:
            st.markdown("<div class='section-title'>Quiet alert state</div>", unsafe_allow_html=True)
            st.metric("State", "alert: beyond band" if is_alert else "quiet")
            st.write(f"- Z-score band: {'beyond band' if is_alert else 'within band or unavailable'}")
            st.write(f"- Liquidity: {'passes for alert' if is_alert else 'not a qualifying liquid alert'}")
            st.write(f"- Clears modeled base costs: {'yes' if not base.empty and bool(base['edge_survives_costs'].iloc[0]) else 'no'}")
            st.caption(f"Raw latest-date signal rows suppressed for this pair: {raw_suppressed}")
        with right:
            st.markdown("<div class='section-title'>Research guardrail</div><p class='section-note'>Alerts are local research watches, not a prediction, execution instruction, or profit claim.</p>", unsafe_allow_html=True)

    with term:
        st.markdown("<div class='section-title'>Term structure</div><p class='section-note'>Latest same-day, expiry-keyed curves from the existing materialized output.</p>", unsafe_allow_html=True)
        st.plotly_chart(_term_structure_chart(term_structure), width="stretch")

    with backtest:
        st.markdown("<div class='section-title'>Backtest after modeled costs</div><p class='section-note'>In-sample and out-of-sample phases are separated using the existing stored attribution.</p>", unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("Base net return", _format_pct(base["net_return"].iloc[0]) if not base.empty else "—")
        metrics[1].metric("Return ex gold move", "Not calculated (no gold-move proxy)")
        metrics[2].metric("Base max drawdown", "—" if max_drawdown is None else f"Rs {max_drawdown:,.0f}")
        metrics[3].metric("Base turnover / entry exposure", "—" if turnover is None else f"{turnover:.2f}x")
        if not phases.empty:
            base_phases = phases[phases["scenario"] == "base"].copy()
            base_phases["net_return"] = base_phases["net_return"].map(_format_pct)
            st.caption("Base scenario, separated by non-overlapping in-sample / out-of-sample signal, entry, and exit phases.")
            st.dataframe(base_phases[["phase", "trades", "gross_pnl", "total_cost", "net_pnl", "net_return"]], width="stretch", hide_index=True)
        if not scenarios.empty:
            scenario_display = scenarios.copy()
            scenario_display["gross_return"] = scenario_display["gross_return"].map(_format_pct)
            scenario_display["net_return"] = scenario_display["net_return"].map(_format_pct)
            st.markdown("<div class='section-title' style='font-size:1rem;margin-top:1.2rem'>Low / base / high cost scenarios</div>", unsafe_allow_html=True)
            st.dataframe(scenario_display, width="stretch", hide_index=True)
            stability = "Yes" if bool(scenarios["verdict_changes_between_scenarios"].iloc[0]) else "No"
            st.caption(f"Verdict changes between scenarios: {stability}.")
        st.warning(f"{verdict} Limits: Close is a declared settlement proxy; execution assumes the next trading day; possible missing expiries are GOLDM Dec 2025 and GOLDPETAL Nov 2026; all four contracts share 387 trading dates from 2025-03-31 to 2026-10-23; and low/base/high cost scenarios are assumptions.")

    with calendar_tab:
        st.markdown("<div class='section-title'>Contract calendar</div><p class='section-note'>Configured windows and events; values labelled unverified have not been independently confirmed.</p>", unsafe_allow_html=True)
        if calendar.empty: st.info("Run the S6 calendar materialization to view configured expiry windows and events.")
        else: st.dataframe(calendar.sort_values(["symbol", "event_type"]), width="stretch", hide_index=True)
        contract_specs = _contracts()
        cards = st.columns(4)
        for column, (symbol, values) in zip(cards, contract_specs.items(), strict=True):
            with column: spec(symbol, values)

    with quality_tab:
        st.markdown("<div class='section-title'>Data quality</div><p class='section-note'>Raw-report checks are recomputed locally from supplied files.</p>", unsafe_allow_html=True)
        with st.expander("Data quality details", expanded=True):
            quality = load_data_quality()
            if not quality: st.info("No raw files are available under data/raw/.")
            else:
                st.write(f"Rows read: {quality['rows_read']:,}; kept: {quality['rows_after_deduplication']:,}; rejected files: {quality['files_rejected']:,}; duplicates removed: {quality['duplicates_removed']:,}.")
                st.write("Expiries per symbol:", quality["expiries_per_symbol"])
                if quality["date_problems"]: st.caption("Rejected/quality notes: " + " | ".join(quality["date_problems"]))

    st.markdown("<div class='footer'><strong>GoldLens · The Backend Bench</strong> · Close is used as a declared settlement proxy; execution defaults to the next trading day; possible missing expiries are GOLDM Dec 2025 and GOLDPETAL Nov 2026; 387 shared trading dates cover 2025-03-31 to 2026-10-23; cost scenarios are assumptions.<br/>Independent prototype, not affiliated with MCX.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
