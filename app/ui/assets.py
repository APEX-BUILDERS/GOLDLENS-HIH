"""Safe, local-only image asset lookup for the Streamlit presentation."""

from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image


APP_DIRECTORY = Path(__file__).resolve().parents[1]


def load_asset(name: str, app_directory: Path = APP_DIRECTORY) -> Path | None:
    """Return a verified local UI asset, or ``None`` without raising."""
    try:
        candidate = app_directory / "assets" / Path(name).name
        if not candidate.is_file():
            return None
        with Image.open(candidate) as image:
            image.verify()
        return candidate
    except (OSError, ValueError):
        return None


def image_data_uri(asset: Path | None) -> str | None:
    """Return a local PNG data URI for controlled inline header presentation."""
    if asset is None:
        return None
    try:
        return "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
    except OSError:
        return None
