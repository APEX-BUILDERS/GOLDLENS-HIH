import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


pytestmark = pytest.mark.skipif(
    os.name == "nt" and "sandbox." in os.environ.get("LOCALAPPDATA", "").lower(),
    reason="Streamlit AppTest cannot create its Windows event-loop socket in the sandbox",
)


def test_dashboard_loads_without_exceptions() -> None:
    app = AppTest.from_file(Path(__file__).parents[1] / "app" / "streamlit_app.py")
    app.run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "GoldLens"
