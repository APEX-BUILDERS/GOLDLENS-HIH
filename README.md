# GoldLens

GoldLens is a rigorous MCX gold-futures comparison prototype. It normalizes quote bases and purity before comparing contract prices, then assesses liquidity, costs, carry, and out-of-sample performance.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
streamlit run app/streamlit_app.py
```

Real MCX Bhavcopy files belong in `data/raw/`; they are required from S1 onward.
