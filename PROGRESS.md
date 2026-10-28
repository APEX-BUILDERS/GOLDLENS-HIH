# GoldLens progress

**Current step:** S12 complete  
**Last task summary:** S12 adds submission-ready documentation, architecture and deployment material, a timed demo script, and GitHub Actions workflows for tests and scheduled local-data rebuilds.  
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
| S7 Walk-forward backtester | done (tests green) | `backtest/` modules; 1,168 real gross, pre-cost trades materialized as `backtest_trades`, with separate non-overlapping `backtest_summary` phases. |
| S8 Cost model and liquidity | done (tests green) | `backtest/costs.py`, `backtest/cost_run.py`, and `config/costs.yml`; scenario-specific real-trade rows are in `backtest_costed_trades` and summaries in `backtest_cost_scenarios`. |
| S9 Attribution | done (tests green) | `backtest/attribution.py` and `backtest/attribution_run.py`; real costed trades are attributed in DuckDB by scenario, phase, and `(left symbol, left expiry, right symbol, right expiry, direction)`. |
| S10 Quiet alerts | done (tests green) | `alerts/quiet.py` and `alerts/run.py`; local-only watches from the latest materialized, liquid, past-only z-scores are stored in `quiet_alerts`. |
| S11 Dashboard | done (tests green) | `app/streamlit_app.py`; cached local DuckDB/raw-data dashboard with expiry-keyed spread/bands/alerts, calendar, costs/backtest, verdict, and data quality. |
| S12 Docs, CI, demo, submission | done (tests green) | Expanded `README.md`; `docs/architecture.md`, `docs/deployment.md`, and `docs/demo_script.md`; `.github/workflows/ci.yml` and `daily_ingest.yml`. |

## Data facts

- Raw files location: `data/raw/`
- All four contracts overlap on 387 trading dates, 2025-03-31 to 2026-10-23.
- Official settlement-price column name: absent from source reports.
- Possible missing expiries: GOLDM Dec 2025; GOLDPETAL Nov 2026.

## TODO(verify)

- Verify contract specifications in `config/contracts.yml` against MCX publications.
- Verify published cost rates in `config/costs.yml` against current MCX, SEBI, tax, state-stamp-duty, and broker material before relying on the reported results. Each is explicitly marked `TODO(verify)`.
- Verify the meaning and units of both `Volume(Lots)` and `Volume(In 000's)`; both are retained without conversion.
- Verify the broker's Rs 20-per-order / 0.03%-of-turnover brokerage cap and the MCX exchange charge against the applicable account and contract schedule.
- Verify the 0.002% buy-side stamp-duty rate; available sources conflict.

## Decisions

- Price proxy: the supplied MCX reports have no official settlement-price column. `Close` is stored as `settlement_proxy` and is never labeled as official settlement. This is a limitation of all downstream results unless official settlement data is later supplied.
- Source validation: filenames and folders are not used as dates. Each HTML-in-XLS report is checked from its internal rows for explicit date parsing, trade date on/before expiry, no weekend dates, one expiry per file, and sparse date density.
- Overlaps: rows are keyed by `(Symbol, Expiry Date, Date)`. Identical overlaps are removed; any disagreement in price fields raises an error.
- Normalization: `settlement_proxy` is converted using each contract's configured `quote_base_grams`, then expressed at 999 purity. `normalized_futures` retains `(Symbol, Expiry Date, Date)` and does not stitch contracts or expiries.
- S4 expiry alignment: pairs join by common trading day and calendar expiry month, but retain both actual expiry dates. This creates all six pairs without treating GOLDM's early-month expiry as the same date as month-end contracts; S5 will model that carry gap explicitly.
- S4 signals: rolling mean and standard deviation use only prior observations within each exact pair-of-expiries series. Default materialization uses a 20-observation window, 10 prior observations minimum, and both legs must have at least one reported volume lot and one open-interest lot to be marked liquid.
- S5 carry/roll-down: each contract's same-day adjacent-expiry slope estimates the left leg's price change over the actual expiry-day gap to the right leg. The raw per-gram quote spread decomposes exactly as `purity component + carry/roll-down component + residual`; 44 real rows have no same-day adjacent curve point, so their carry and residual are left null rather than inferred.
- S6 calendar: expiry windows are configured in `config/contracts.yml` and returned as windows rather than invented exact expiry days. A current MCX market-data reference is recorded there; listing and tender rules/dates have no verified circular source yet, so all twelve associated events remain `TODO(verify)` with null dates.
- S7 execution: z-scores are recalculated from prior observations only for each exact expiry pair. A qualifying signal at day t enters at the next observed trading day and exits one observed trading day later; sizing uses whole lots with the closest notionals at or below the configured target. The current replay uses Rs 20,000,000 target notional, a 20/10 rolling window, 2.0 z-score threshold, and 31 March 2026 train end. A trade is retained only if its signal, entry, and exit all fall on the same side of the train/test boundary; 1,168 real trades remain gross and pre-cost only before S8 applies costs and thin-day treatment.
- S8 costs: the model charges per-executed-order brokerage at the lower of 0.03% turnover and Rs 20, MCX exchange charges, SEBI Rs 10 per crore turnover, GST at 18% on brokerage/exchange/SEBI charges only, seller-side CTT at 0.01%, buyer-side stamp duty at 0.002%, entry-notional margin financing over actual calendar holding days, slippage, and a threshold-triggered thin-day haircut. Cost rates are loaded only from `config/costs.yml`; published values are marked `TODO(verify)` rather than treated as settled facts.
- S8 scenario assumptions: low/base/high annual margin rates are 6%/10%/16%. GOLDM and GOLDTEN slippage is 1/2/4 bps and thin-day haircut is 2/5/10 bps; GOLDGUINEA and GOLDPETAL slippage is 2/5/10 bps and thin-day haircut is 4/10/20 bps.
- S8 real-data results (all 1,168 S7 trades; aggregate P&L divided by aggregate entry exposure): low gross 0.037327%, net -0.034620% (Rs 8,040,479.48 / -Rs 7,457,483.65); base gross 0.037327%, net -0.091167% (Rs 8,040,479.48 / -Rs 19,638,273.90); high gross 0.037327%, net -0.186004% (Rs 8,040,479.48 / -Rs 40,066,866.55). `edge_survives_costs` is false in all three; verdict changes between scenarios: false.
- S9 attribution: `backtest_attribution_overall` has three scenario rows, `backtest_attribution_phase` has six rows, and `backtest_attribution_expiry_pair` has 738 exact-expiry-pair rows. The regenerated overall totals are low: gross Rs 8,040,479.48, costs Rs 15,497,963.13, net -Rs 7,457,483.65; base: gross Rs 8,040,479.48, costs Rs 27,678,753.38, net -Rs 19,638,273.90; high: gross Rs 8,040,479.48, costs Rs 48,107,346.03, net -Rs 40,066,866.55. Maximum absolute P&L or cost reconciliation difference at the expiry-pair level is below Rs 0.000000001 due to floating-point arithmetic.
- S10 quiet alerts: the runner reads only the newest date already present in `spread_signals`, filters to liquid rows whose past-only absolute z-score meets the configured threshold (default 2.0), and writes a local `quiet_alerts` table. It never predicts a price, sends a notification, chooses an execution date, or submits an order. At the current real-data cutoff (2026-10-23), it wrote one watch: GOLDGUINEA 2026-10-30 versus GOLDPETAL 2026-10-30, z-score -2.431214. The stored message explicitly states that it is not a prediction, execution instruction, or profit claim.
- Look-ahead audit: S4 rolling mean and standard deviation use `shift(1)` within each exact expiry pair. S7 re-computes those past-only scores, enters only on the next observed trading day, and now drops signals whose entry/exit crosses `train_end`; attribution aggregates stored costs/P&L only, and has no gold-move proxy, beta, model fit, or full-sample statistic. S10 accepts an optional `as_of` cutoff and filters rows to that date or earlier before creating a watch. The audit found no other look-ahead paths.
- S11 dashboard: `app/streamlit_app.py` uses `st.cache_data` for DuckDB tables and the raw-report quality summary. The spread panel retains each exact expiry pair as a separate Plotly trace and prior-only normal band—no stitched series. The default selector is GOLDTEN versus GOLDPETAL. The backtest panel labels return ex gold move as unavailable because no proxy is modeled. The S11 AppTest smoke test runs on ordinary environments; this sandbox skips it because Streamlit's in-process test runner cannot create its required Windows event-loop socket. A direct launcher reached Streamlit's server event-loop startup here, but sandbox networking prevented a localhost readiness probe. The final suite result is 29 passed, 1 skipped (the environment-specific AppTest), and 1 sandbox pytest-cache warning.

## Commands that work

- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q`
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m streamlit run app/streamlit_app.py`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.ingest.run --raw data/raw`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.normalize.run --db data/goldlens.duckdb --contracts config/contracts.yml`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.analytics.run --db data/goldlens.duckdb --window 20 --min-periods 10 --min-volume-lots 1 --min-open-interest-lots 1`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.analytics.term_structure_run --db data/goldlens.duckdb`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.calendar.run --db data/goldlens.duckdb --contracts config/contracts.yml --as-of 2026-10-27`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.backtest.run --db data/goldlens.duckdb --contracts config/contracts.yml --window 20 --min-periods 10 --zscore-threshold 2 --target-notional 20000000 --train-end 2026-03-31`
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.backtest.cost_run --db data/goldlens.duckdb --costs config/costs.yml --min-volume-lots 1 --min-open-interest-lots 1` (writes real-trade low/base/high cost scenarios and prints the report)
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.backtest.attribution_run --db data/goldlens.duckdb` (materializes S9 attribution from the S8 real-trade rows)
- `$env:PYTHONPATH = 'src'; C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m goldlens.alerts.run --db data/goldlens.duckdb --zscore-threshold 2` (materializes local-only S10 research watches; sends no notification)
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m streamlit run app/streamlit_app.py` (launches the local S11 dashboard)
- `C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest -q --basetemp .pytest-tmp` (the sandbox blocks pytest's default system-temp path)

## Files changed in S8

- `config/costs.yml`
- `src/goldlens/backtest/costs.py`
- `src/goldlens/backtest/cost_run.py`
- `tests/test_costs.py`
- `src/goldlens/ingest/pipeline.py`
- `PROGRESS.md`

## Files changed in S9

- `src/goldlens/backtest/attribution.py`
- `src/goldlens/backtest/attribution_run.py`
- `tests/test_attribution.py`
- `PROGRESS.md`

## Files changed in S10

- `src/goldlens/alerts/__init__.py`
- `src/goldlens/alerts/quiet.py`
- `src/goldlens/alerts/run.py`
- `tests/test_quiet_alerts.py`
- `PROGRESS.md`

## Files changed in the look-ahead audit

- `src/goldlens/backtest/walk_forward.py`
- `src/goldlens/alerts/quiet.py`
- `src/goldlens/alerts/run.py`
- `tests/test_walk_forward.py`
- `tests/test_quiet_alerts.py`
- `PROGRESS.md`

## Files changed in S11

- `app/streamlit_app.py`
- `tests/test_dashboard.py`
- `PROGRESS.md`

## Files changed in S12

- `README.md`
- `docs/architecture.md`
- `docs/deployment.md`
- `docs/demo_script.md`
- `.github/workflows/ci.yml`
- `.github/workflows/daily_ingest.yml`
- `PROGRESS.md`

## Next step

Submission readiness: push the S12 commit, let CI run, verify TODO(verify) inputs against current MCX and broker material, and deploy only after the real-data DuckDB tables have been rebuilt from `data/raw/`.

## UI polish baseline and completion (2026-10-28)

- Before the presentation-only dashboard work, the suite result was 29 passed, 1 skipped, 1 environment-specific pytest-cache warning. The recorded default-dashboard values were: base net return `-0.0912%`; return ex gold move `Not calculated (no gold-move proxy)`; base maximum drawdown `Rs -19,618,332`; turnover / entry exposure `2.00x`; verdict `The modeled base-case edge does not survive costs.`; alert state `quiet`; and raw latest-date signal rows suppressed `4`.
- UI-only work added the deep-navy utility/header treatment, styled tabs, overview hero with original inline-SVG bars, product chips using existing normalized outputs, shared Plotly presentation styling, tabbed spread/term-structure/backtest/calendar/data-quality views, contract specification cards with unverified values explicitly labelled, and the limitations footer. No computations, input data, configuration values, or existing test expectations were changed.
- A new `tests/test_dashboard_ui_smoke.py` checks the six research tabs with `streamlit.testing.v1.AppTest`. In this Windows sandbox both AppTest smoke tests are skipped because Streamlit cannot create its event-loop socket, which is the same established environment limitation. The final suite was 29 passed, 2 skipped, 1 pytest-cache warning. A value-level post-change check exactly matched the recorded baseline values and verdict text above.

## Dashboard logo baseline and completion (2026-10-28)

- Before the logo-only work, the suite result was 29 passed, 2 skipped, 1 environment-specific pytest-cache warning. The dashboard values recorded again were: base net return `-0.0912%`; return ex gold move `Not calculated (no gold-move proxy)`; base maximum drawdown `Rs -19,618,332`; turnover / entry exposure `2.00x`; verdict `The modeled base-case edge does not survive costs.`; alert state `quiet`; and raw latest-date signal rows suppressed `4`.
- The white header now uses the verified local `app/assets/logo.png` at approximately 220 px. `app/ui/assets.py` resolves image paths relative to the app directory, verifies image files, and safely returns `None` on a missing or invalid asset; the header then renders the `Gold` / `Lens` text fallback without raising. `favicon.png` is supplied to `st.set_page_config` as the page icon. Dark hero and footer areas use text-only GoldLens branding, never the white-background logo.
- The README now uses the GitHub-compatible repository-relative Markdown path `app/assets/logo.png`. The logo asset test verifies all three supplied logo files and the missing-asset fallback.
- Final suite result: 31 passed, 2 skipped, 1 environment-specific pytest-cache warning. The direct AppTest attempt was unable to return in this Windows sandbox (the established Streamlit event-loop limitation); its two repository smoke tests remain safely skipped here. A direct headless Streamlit process ran without emitted startup errors before being stopped. The post-change value-level check exactly matched the baseline above.
