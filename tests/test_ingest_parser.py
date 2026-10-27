from pathlib import Path

import pytest

from goldlens.ingest.date_utils import DateValidationError
from goldlens.ingest.parser import parse_bhavcopy_file


FIXTURES = Path(__file__).parent / "fixtures"


def test_date_mismatch_is_rejected() -> None:
    with pytest.raises(DateValidationError, match="Requested date"):
        parse_bhavcopy_file(FIXTURES / "daily_mismatch_02012025.csv")


def test_only_target_symbols_kept() -> None:
    frame, summary = parse_bhavcopy_file(FIXTURES / "daily_01012025.csv")

    assert frame["Symbol"].tolist() == ["GOLDTEN"]
    assert summary.rows_read == 3
    assert summary.rows_kept == 1
    assert frame["settlement_proxy"].tolist() == [80000]
