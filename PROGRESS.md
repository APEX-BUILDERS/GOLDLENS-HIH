# GoldLens progress

**Current step:** S8  
**Last task summary:** S8 cost engine is implemented and tested, but real net results are blocked until six account- or execution-specific rates are verified in `config/costs.yml`.  
**Last agent/LLM used:** Codex

## Step status

| Step | Status | Files created / notes |
|---|---|---|
| S0 Setup and contract config | done (tests green) | `requirements.txt`, configs, contract registry, Streamlit hello page, and contract-config test. |
| S1 Ingest with date validation | done (tests green) | Internal formats and consistency checks; no filename or folder date logic. |
| S2 Cleaning and storage | done (tests green) | Conflict-safe overlap dedupe and `data/goldlens.duckdb` clean table. |
| S3 Normalization engine | done (tests green) | `normalize/per_gram.py`, `normalize/purity.py`, and `normalize/run.py`; real results materialized as DuckDB table `normalized_futures`. |
| S4 Spreads and z-scores | done (tests green) | `analytics/spreads.py`, `analytics/liquidity.py`, `analytics/zscore.py`, and `analytics/run.py`; 11,215 real rows in `spread_signals`. |
| S5 Term structure and carry | done (tests green) | `analytics/term_structure.py` and `analytics/term_structure_run.py`; 8,740 term-structure rows and 11,215 decompositions stored in DuckDB. |
| S6 Contract calendar | done (tests green) | `calendar/contract_calendar.py` and `calendar/run.py`; DuckDB calendar stores four upcoming expiry windows and twelve TODO(verify) event entries. |
| S7 Walk-forward backtester | done (tests green) | `backtest/` modules; 1,192 real gross, pre-cost trades materialized as `backtest_trades`, with separate `backtest_summary` phases. |
| S8 Cost model and liquidity | blocked (rate inputs needed) | `backtest/costs.py` and `backtest/cost_run.py`; full cost model rejects unverified config instead of publishing invented net results. |
| S9-S12 | not started | |

## Data facts

- Raw files location: `data/raw/`
- Date range covered: common four-symbol dates: 2025-03-31 to 2026-10-23 (386 after removing invalid weekend rows).
- Official settlement-price column name: absent from source reports.
- Symbols and expiries found: GOLDGUINEA (27), GOLDM (27), GOLDPETAL (25), GOLDTEN (24) expiries. Gaps: GOLDM 2025-12; GOLDPETAL 2026-11.

## TODO(verify)

- Verify contract specifications in `config/contracts.yml` against MCX publications.
- Verify cost rates and dates/sources in `config/costs.yml` before reporting results.
- Verify the meaning and units of both `Volume(Lots)` and `Volume(In 000's)`; both are retained without conversion.
- Fill and source `brokerage_rate`, `exchange_charge_rate`, `stamp_duty_rate`, `slippage_bps`, `margin_rate`, and `thin_day_haircut_bps` in `config/costs.yml`. The S8 runner refuses real net P&L until these are verified.

## Decisions

- Price proxy: the supplied MCX reports have no official settlement-price column. `Close` is stored as `settlement_proxy` and is never labeled as official settlement. This is a limitation of all downstream results unless official settlement data is later supplied.
- Source validation: filenames and folders are not used as dates. Each HTML-in-XLS report is checked from its internal rows for explicit date parsing, trade date on/before expiry, no weekend dates, one expiry per file, and sparse date density.
- Overlaps: rows are keyed by `(Symbol, Expiry Date, Date)`. Identical overlaps are removed; any disagreement in price fields raises an error.
- Normalization: `settlement_proxy` is converted using each contract's configured `quote_base_grams`, then expressed at 999 purity. `normalized_futures` retains `(Symbol, Expiry Date, Date)` and does not stitch contracts or expiries.
- S4 expiry alignment: pairs join by common trading day and calendar expiry month, but retain both actual expiry dates. This creates all six pairs without treating GOLDM's early-month expiry as the same date as month-end contracts; S5 will model that carry gap explicitly.
- S4 signals: rolling mean and standard deviation use only prior observations within each exact pair-of-expiries series. Default materialization uses a 20-observation window, 10 prior observations minimum, and both legs must have at least one reported volume lot and one open-interest lot to be marked liquid.
- S5 carry/roll-down: each contract's same-day adjacent-expiry slope estimates the left leg's price change over the actual expiry-day gap to the right leg. The raw per-gram quote spread decomposes exactly as `purity component + carry/roll-down component + residual`; 44 real rows have no same-day adjacent curve point, so their carry and residual are left null rather than inferred.
- S6 calendar: expiry windows are configured in `config/contracts.yml` and returned as windows rather than invented exact expiry days. A current MCX market-data reference is recorded there; listing and tender rules/dates have no verified circular source yet, so all twelve associated events remain `TODO(verify)` with null dates.
- S7 execution: z-scores are recalculated from prior observations only for each exact expiry pair. A qualifying signal at day t enters at the next observed trading day and exits one observed trading day later; sizing uses whole lots with the closest notionals at or below the configured target. The current replay uses Rs 20,000,000 target notional, a 20/10 rolling window, 2.0 z-score threshold, and 31 March 2026 train end. Its 1,192 trades are gross and pre-cost only; S8 must apply costs and thin-day treatment before interpreting performance.
- S8 costs: the model charges brokerage, exchange, GST on brokerage/exchange charges, seller-side CTT, buyer-side stamp duty, entry-notional margin financing over actual calendar holding days, slippage, and a threshold-triggered thin-day haircut. CTT is configured at 0.01% seller-side from Income Tax Act section 117; GST is 18% on service charges based on CBIC guidance. The remaining rates are not public/account-independent facts and stay null pending verification.

## Commands that work

- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m streamlit run app/streamlit_app.py`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.ingest.run --raw data/raw`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.normalize.run --db data/goldlens.duckdb --contracts config/contracts.yml`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.analytics.run --db data/goldlens.duckdb --window 20 --min-periods 10 --min-volume-lots 1 --min-open-interest-lots 1`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.analytics.term_structure_run --db data/goldlens.duckdb`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.calendar.run --db data/goldlens.duckdb --contracts config/contracts.yml --as-of 2026-10-27`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.backtest.run --db data/goldlens.duckdb --contracts config/contracts.yml --window 20 --min-periods 10 --zscore-threshold 2 --target-notional 20000000 --train-end 2026-03-31`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.backtest.cost_run --db data/goldlens.duckdb --costs config/costs.yml --min-volume-lots 1 --min-open-interest-lots 1` (runs only after all cost fields are verified)
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp .pytest-tmp` (the sandbox blocks pytest's default system-temp path)

## Next step

S8: unblock by filling and sourcing the six missing cost/execution parameters in `config/costs.yml`, then materialize gross and net performance side by side.
