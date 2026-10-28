![GoldLens logo](app/assets/logo.png)

# GoldLens

GoldLens is a research prototype for comparing the four MCX gold futures contracts—GOLDM, GOLDTEN, GOLDGUINEA, and GOLDPETAL—on a like-for-like basis. It is not a price-prediction system, an execution service, or a profit claim.

The prototype first normalizes each futures quote to rupees per gram at 999 purity, retains every `(symbol, expiry_date)` series separately, and then evaluates apparent relative-value signals after expiry/carry, liquidity, whole-lot sizing, and trading-cost adjustments.

## Key finding

On the supplied real Bhavcopy reports through 23 October 2026, the current walk-forward replay produces a small positive gross result but a negative net result in every configured cost scenario. The present conclusion is therefore **no persistent edge survives the modeled costs**. This is a research result, not investment advice. See [PROGRESS.md](PROGRESS.md) for the recorded figures, assumptions, and data-quality facts.

## Method

1. Validate internally reported dates and retain only the four target futures contracts.
2. Store clean rows in DuckDB, keyed by symbol, expiry date, and trade date.
3. Normalize quote bases and purity before forming a spread.
4. Calculate exact-expiry-pair spreads and bands using prior observations only.
5. Decompose the observed spread into purity, carry/roll-down, and residual components where the curve data permits it.
6. Replay qualifying signals with next-observed-trading-day execution and whole-lot, matched-notional legs.
7. Apply brokerage, exchange/SEBI charges, GST, CTT, stamp duty, slippage, margin financing, and thin-day haircuts from [config/costs.yml](config/costs.yml).

There is no stitched near-month series anywhere in the signal or result path.

## Run locally

Requires Python 3.11+ and the real reports under `data/raw/`. A fresh clone contains the tracked reports used for the prototype; replace or add files only with public MCX Bhavcopy data.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Build the local DuckDB file from the real reports and materialize the research tables:

```powershell
$env:PYTHONPATH = 'src'
python -m goldlens.ingest.run --raw data/raw --db data/goldlens.duckdb
python -m goldlens.normalize.run --db data/goldlens.duckdb --contracts config/contracts.yml
python -m goldlens.analytics.run --db data/goldlens.duckdb --window 20 --min-periods 10 --min-volume-lots 1 --min-open-interest-lots 1
python -m goldlens.analytics.term_structure_run --db data/goldlens.duckdb
python -m goldlens.calendar.run --db data/goldlens.duckdb --contracts config/contracts.yml --as-of 2026-10-27
python -m goldlens.backtest.run --db data/goldlens.duckdb --contracts config/contracts.yml --window 20 --min-periods 10 --zscore-threshold 2 --target-notional 20000000 --train-end 2026-03-31
python -m goldlens.backtest.cost_run --db data/goldlens.duckdb --costs config/costs.yml --min-volume-lots 1 --min-open-interest-lots 1
python -m goldlens.backtest.attribution_run --db data/goldlens.duckdb
python -m goldlens.alerts.run --db data/goldlens.duckdb --zscore-threshold 2
streamlit run app/streamlit_app.py
```

The dashboard reads only local DuckDB tables and local raw-report quality checks; it does not call a network data source or submit orders.

## Limits and verification required

- Source reports do not include an official settlement column, so `Close` is explicitly stored as a settlement proxy.
- Contract specifications, listing/tender rules, and several cost inputs are marked `TODO(verify)` in configuration and in [PROGRESS.md](PROGRESS.md).
- Reported volume is a liquidity filter, not order-book depth.
- Results cover the supplied reports only and do not establish future performance.

## Project materials

- [Architecture](docs/architecture.md)
- [Streamlit Community Cloud deployment notes](docs/deployment.md)
- [2–3 minute demo script](docs/demo_script.md)
- [Build plan](docs/PLAN.md)
