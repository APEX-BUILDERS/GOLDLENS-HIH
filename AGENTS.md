# GoldLens agent guide

GoldLens compares MCX gold futures only after quote-base, purity, expiry, liquidity, and trading-cost adjustments. It is not a price-prediction or profit bot.

Work one numbered step at a time. Maintain expiry-keyed series; never use a stitched near-month series. Signals may use only data available through the signal date, and execution defaults to the next trading day. Results must use real files supplied under `data/raw/`; fixtures are test-only. Contract specifications and trading costs belong only in `config/`.

The fixed stack is Python 3.11+, pandas, NumPy, DuckDB, Streamlit, Plotly, PyYAML, pytest, and optional scikit-learn. Update `PROGRESS.md`, run `pytest -q`, and make one commit per completed step.
