# GoldLens architecture

```mermaid
flowchart LR
    raw["Public MCX Bhavcopy reports\ndata/raw/"] --> ingest["Ingest and validation\ninternal dates · target contracts"]
    config["Configuration\ncontracts.yml · costs.yml"] --> normalize["Quote-base and purity\nnormalization"]
    ingest --> clean["Clean expiry-keyed rows\nDuckDB: clean_futures"]
    clean --> normalize
    normalize --> futures["DuckDB: normalized_futures\n(symbol, expiry, date)"]
    futures --> spreads["Spreads, liquidity and\npast-only z-scores"]
    futures --> curve["Term structure and\ncarry decomposition"]
    spreads --> replay["Walk-forward replay\nnext-day execution · whole lots"]
    config --> replay
    replay --> costs["Scenario cost model\nand thin-day haircut"]
    config --> costs
    costs --> attribution["Cost attribution\nand verdict inputs"]
    spreads --> alerts["Quiet research watches\nliquidity + band checks"]
    curve --> dashboard["Streamlit + Plotly\nlocal dashboard"]
    attribution --> dashboard
    alerts --> dashboard
    clean --> dashboard
```

## Guardrails

- Every analytical table keeps its actual expiry date. The system never constructs a stitched near-month series.
- Signal bands are calculated from observations available on or before the signal date; execution is on the next observed trading day.
- Costs are loaded only from `config/costs.yml`; contract details are loaded only from `config/contracts.yml`.
- The dashboard and published results read real local reports and DuckDB tables, never test fixtures.
