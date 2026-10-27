from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
frames = []
cols_seen = set()

for folder in sorted(p for p in RAW.iterdir() if p.is_dir() and not p.name.startswith("OPTCOM")):
    for f in sorted(folder.glob("*.xls*")):
        try:
            df = pd.read_html(f)[0]
        except Exception as e:
            print("READ ERROR:", folder.name, f.name, str(e)[:80])
            continue
        df.columns = [str(c).strip() for c in df.columns]
        cols_seen.add(tuple(df.columns))
        df["_folder"] = folder.name
        df["_file"] = f.name
        frames.append(df)

d = pd.concat(frames, ignore_index=True)
d["dt"] = pd.to_datetime(d["Date"], dayfirst=True, errors="coerce")
d["exp"] = pd.to_datetime(d["Expiry Date"], dayfirst=True, errors="coerce")
print("Unparsable dates:", int(d["dt"].isna().sum()), "| unparsable expiries:", int(d["exp"].isna().sum()))

print("\n== COLUMNS SEEN ==")
for c in cols_seen:
    print(list(c))

print("\n== INSTRUMENTS ==", sorted(map(str, d["Instrument Name"].dropna().unique())))

print("\n== PER SYMBOL ==")
g = d.groupby("Symbol").agg(files=("_file", "nunique"), rows=("dt", "size"),
                            first=("dt", "min"), last=("dt", "max"),
                            expiries=("exp", "nunique"))
print(g.to_string())

print("\n== EXPIRIES PER SYMBOL ==")
for s, sub in d.groupby("Symbol"):
    print(s, sorted(x.strftime("%Y-%m-%d") for x in sub["exp"].dropna().unique()))

print("\n== FILES WITH MORE THAN ONE EXPIRY (anomalies) ==")
fx = d.groupby(["_folder", "_file"]).agg(n_exp=("exp", "nunique"), rows=("dt", "size"),
                                         n_dates=("dt", "nunique"))
print(fx[fx["n_exp"] != 1].to_string())

print("\n== COMMON DATES ACROSS ALL SYMBOLS ==")
sets = {s: set(sub["dt"].dropna()) for s, sub in d.groupby("Symbol")}
common = set.intersection(*sets.values()) if sets else set()
print("symbols:", list(sets), "| dates present in all:", len(common))
if common:
    print("from", min(common).date(), "to", max(common).date())

print("\n== DUPLICATE (Symbol, expiry, date) ROWS ACROSS FILES ==")
dup = d[d.duplicated(["Symbol", "exp", "dt"], keep=False)]
print("duplicate rows:", len(dup))
if "Close" in d.columns and len(dup):
    diff = dup.groupby(["Symbol", "exp", "dt"])["Close"].nunique()
    print("keys with DIFFERENT Close values:", int((diff > 1).sum()))