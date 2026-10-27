from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
rows = []

for folder in sorted(p for p in RAW.iterdir() if p.is_dir() and not p.name.startswith("OPTCOM")):
    for f in sorted(folder.glob("*.xls*")):
        try:
            df = pd.read_html(f)[0]
        except Exception as e:
            rows.append({"folder": folder.name, "file": f.name, "error": str(e)[:80]})
            continue
        dates = pd.to_datetime(df.get("Date"), dayfirst=True, errors="coerce")
        rows.append({
            "folder": folder.name,
            "file": f.name,
            "rows": len(df),
            "cols": "|".join(map(str, df.columns)),
            "instruments": "|".join(sorted(map(str, df.get("Instrument Name", pd.Series()).dropna().unique())))[:60],
            "symbols": "|".join(sorted(map(str, df.get("Symbol", pd.Series()).dropna().unique())))[:60],
            "option_types": "|".join(sorted(map(str, df.get("Option Type", pd.Series()).dropna().unique())))[:30],
            "first_date": dates.min(),
            "last_date": dates.max(),
            "n_dates": dates.nunique(),
            "raw_date_sample": str(df.get("Date", pd.Series()).iloc[0]) if len(df) else "",
        })

out = pd.DataFrame(rows)
out.to_csv("inspect_summary.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 40, "display.max_rows", 500)
print(out.drop(columns=["cols"], errors="ignore").to_string(index=False))
print("\nCOLUMNS SEEN:")
print(out["cols"].dropna().unique() if "cols" in out else "none")