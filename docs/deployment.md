# Streamlit Community Cloud deployment notes

## Before deploying

1. Push the repository, including the public `data/raw/` reports required to rebuild the local research database. Do not add account credentials, API keys, or proprietary market data.
2. Confirm the deployment branch runs `pytest -q` and the materialization commands in the README from a clean checkout.
3. Verify the `TODO(verify)` contract and cost inputs in `config/` before representing any result as current.

## App settings

- Repository: this GoldLens repository
- Main file path: `app/streamlit_app.py`
- Python version: 3.11 or later
- Dependencies: `requirements.txt`

The dashboard needs `data/goldlens.duckdb`. It is deliberately local and ignored by Git, because it is a build artifact rather than a source of truth. Streamlit Community Cloud starts the app but does not provide a general pre-start command for this pipeline. Therefore the current repository is ready for local deployment only: before deploying to Community Cloud, add a reviewed, local start-time bootstrap that runs the README materialization pipeline when the database is absent, or provide a secure public build artifact. Do not replace this with a live data download.

## Operational notes

- This prototype does not download Bhavcopies. Add reviewed public reports to `data/raw/`, then let the scheduled workflow rebuild and validate the tables.
- Do not configure secrets: the app has no external API or broker connection.
- Restart/redeploy after changing raw reports, contract specifications, or cost assumptions so the local cache and DuckDB tables are rebuilt.
- The dashboard is research-only. Its watch rows are not trading instructions and it must not be presented as a profit forecast.
