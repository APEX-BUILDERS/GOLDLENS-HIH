# GoldLens progress

**Current step:** S4  
**Last task summary:** S3 complete: 8,740 real expiry-keyed clean rows were normalized to per-gram values and a common 999 purity basis in DuckDB.  
**Last agent/LLM used:** Codex

## Step status

| Step | Status | Files created / notes |
|---|---|---|
| S0 Setup and contract config | done (tests green) | `requirements.txt`, configs, contract registry, Streamlit hello page, and contract-config test. |
| S1 Ingest with date validation | done (tests green) | Internal formats and consistency checks; no filename or folder date logic. |
| S2 Cleaning and storage | done (tests green) | Conflict-safe overlap dedupe and `data/goldlens.duckdb` clean table. |
| S3 Normalization engine | done (tests green) | `normalize/per_gram.py`, `normalize/purity.py`, and `normalize/run.py`; real results materialized as DuckDB table `normalized_futures`. |
| S4-S12 | not started | |

## Data facts

- Raw files location: `data/raw/`
- Date range covered: common four-symbol dates: 2025-03-31 to 2026-10-23 (386 after removing invalid weekend rows).
- Official settlement-price column name: absent from source reports.
- Symbols and expiries found: GOLDGUINEA (27), GOLDM (27), GOLDPETAL (25), GOLDTEN (24) expiries. Gaps: GOLDM 2025-12; GOLDPETAL 2026-11.

## TODO(verify)

- Verify contract specifications in `config/contracts.yml` against MCX publications.
- Verify cost rates and dates/sources in `config/costs.yml` before reporting results.
- Verify the meaning and units of both `Volume(Lots)` and `Volume(In 000's)`; both are retained without conversion.

## Decisions

- Price proxy: the supplied MCX reports have no official settlement-price column. `Close` is stored as `settlement_proxy` and is never labeled as official settlement. This is a limitation of all downstream results unless official settlement data is later supplied.
- Source validation: filenames and folders are not used as dates. Each HTML-in-XLS report is checked from its internal rows for explicit date parsing, trade date on/before expiry, no weekend dates, one expiry per file, and sparse date density.
- Overlaps: rows are keyed by `(Symbol, Expiry Date, Date)`. Identical overlaps are removed; any disagreement in price fields raises an error.
- Normalization: `settlement_proxy` is converted using each contract's configured `quote_base_grams`, then expressed at 999 purity. `normalized_futures` retains `(Symbol, Expiry Date, Date)` and does not stitch contracts or expiries.

## Commands that work

- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m streamlit run app/streamlit_app.py`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.ingest.run --raw data/raw`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.normalize.run --db data/goldlens.duckdb --contracts config/contracts.yml`
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp .pytest-tmp` (the sandbox blocks pytest's default system-temp path)

## Next step

S4: calculate all six expiry-matched spreads in basis points, past-only rolling z-scores, and volume/open-interest liquidity filters.
