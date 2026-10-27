"""Generate data/raw/manifest.csv from MCX Bhavcopy filenames (DDMMYYYY).
Run from the repo root: python tools/make_manifest.py
"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

RAW = Path("data/raw")
OUT = RAW / "manifest.csv"
PATTERN = re.compile(r"(\d{8})(?:\s*\(\d+\))?\.(xls|xlsx|csv)$", re.IGNORECASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows, problems, seen = [], [], {}
    for p in sorted(RAW.rglob("*")):
        if not p.is_file() or p.name == "manifest.csv":
            continue
        if p.suffix.lower() not in {".xls", ".xlsx", ".csv"}:
            continue
        m = PATTERN.search(p.name)
        if not m:
            problems.append(f"No DDMMYYYY date in filename: {p}")
            continue
        try:
            d = datetime.strptime(m.group(1), "%d%m%Y").date()
        except ValueError:
            problems.append(f"Invalid date in filename: {p}")
            continue
        rel = p.relative_to(RAW).as_posix()
        key = (p.parent.name, d)
        digest = sha(p)
        if key in seen:
            prev_rel, prev_digest = seen[key]
            kind = "identical" if digest == prev_digest else "DIFFERENT content"
            problems.append(f"Duplicate {d} in {p.parent.name}: {prev_rel} and {rel} ({kind})")
        else:
            seen[key] = (rel, digest)
        rows.append((rel, d.isoformat()))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "requested_date"])
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")
    if problems:
        print("\nCheck these:")
        for line in problems:
            print(" -", line)


if __name__ == "__main__":
    main()