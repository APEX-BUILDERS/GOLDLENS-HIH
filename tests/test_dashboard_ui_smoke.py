"""Presentation smoke test for the dashboard's polished tab shell."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


pytestmark = pytest.mark.skipif(
    os.name == "nt" and "sandbox." in os.environ.get("LOCALAPPDATA", "").lower(),
    reason="Streamlit AppTest cannot create its Windows event-loop socket in the sandbox",
)


def test_polished_dashboard_has_all_research_tabs() -> None:
    app = AppTest.from_file(Path(__file__).parents[1] / "app" / "streamlit_app.py")
    app.run(timeout=30)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "Spreads",
        "Term Structure",
        "Backtest",
        "Calendar",
        "Data Quality",
    ]
