import pandas as pd
from pathlib import Path
f = Path("data/raw/FUTCOM-GOLDM/BhavCopyCommodiyWise_01012025(4).xls")
df = pd.read_html(f)[0]
print(len(df))
print(df[["Date", "Expiry Date"]].head(15).to_string())
print(df["Date"].astype(str).str.len().value_counts())