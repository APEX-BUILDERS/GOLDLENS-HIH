from pathlib import Path

import pandas as pd
import pytest

from goldlens.ingest.pipeline import deduplicate_rows, parse_report


def test_sparse_distinct_dates_are_rejected() -> None:
    fixture = Path(__file__).parent / "fixtures" / "suspect_date_density.xls"
    with pytest.raises(ValueError, match="suspect date density"):
        parse_report(fixture)


def test_conflicting_overlap_is_rejected() -> None:
    rows = pd.DataFrame({
        "Symbol": ["GOLDTEN", "GOLDTEN"],
        "Expiry Date": [pd.Timestamp("2025-04-30")] * 2,
        "Date": [pd.Timestamp("2025-03-31")] * 2,
        "Open": [1.0, 1.0], "High": [2.0, 2.0], "Low": [1.0, 1.0],
        "Close": [1.0, 1.1], "Previous Close": [1.0, 1.0],
    })
    with pytest.raises(ValueError, match="conflicting duplicate prices"):
        deduplicate_rows(rows)
