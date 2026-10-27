# GoldLens implementation plan

S0 creates the skeleton and configuration. S1-S2 ingest and clean real MCX Bhavcopy futures data into expiry-keyed DuckDB rows. S3 normalizes price per gram and purity. S4-S5 calculate no-look-ahead spreads, z-scores, term structure, and carry. S6 adds a contract calendar. S7-S9 implement walk-forward testing, costs/liquidity, and attribution. S10-S12 add quiet alerts, dashboard, documentation, CI, and demo materials.

No dashboard, backtest, or reported result may use invented data.
