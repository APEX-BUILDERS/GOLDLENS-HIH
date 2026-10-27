from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

def sniff(path: Path) -> str:
    head = path.read_bytes()[:2000]
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "real-xls"
    if head.startswith(b"PK"):
        return "xlsx"
    low = head.lower()
    if b"<html" in low or b"<table" in low or b"<?xml" in low:
        return "html-or-xml"
    return "text"

for folder in sorted(p for p in RAW.iterdir() if p.is_dir() and not p.name.startswith("OPTCOM")):
    files = sorted(folder.glob("*.xls*"))
    print("\n=====", folder.name, "|", len(files), "files")
    for f in files[:2]:
        kind = sniff(f)
        print("--", f.name, "| size", f.stat().st_size, "| looks like:", kind)
        raw = f.read_bytes()[:700].decode("utf-8", errors="replace")
        print("RAW START:\n", raw)
        try:
            if kind == "real-xls":
                df = pd.read_excel(f, header=None, engine="xlrd")
            elif kind == "xlsx":
                df = pd.read_excel(f, header=None, engine="openpyxl")
            elif kind == "html-or-xml":
                df = pd.read_html(f)[0]
            else:
                df = pd.read_csv(f, sep=None, engine="python", header=None)
            print("PARSED shape:", df.shape)
            print(df.head(6).to_string())
        except Exception as e:
            print("PARSE ERROR:", e)