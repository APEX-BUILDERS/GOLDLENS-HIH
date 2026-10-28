"""Local asset and fallback smoke tests for the dashboard logo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
from ui.assets import load_asset


def test_dashboard_logo_assets_exist() -> None:
    assert load_asset("logo.png") is not None
    assert load_asset("favicon.png") is not None
    assert load_asset("icon_128.png") is not None


def test_missing_dashboard_asset_uses_safe_fallback() -> None:
    assert load_asset("not-present.png", Path("definitely-not-an-app-directory")) is None
