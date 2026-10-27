"""Load the configured MCX gold contract registry."""

from pathlib import Path
from typing import Any

import yaml


REQUIRED_CONTRACT_KEYS = {"lot_unit_grams", "quote_base_grams", "purity", "expiry_window"}


def load_contracts(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load and validate contract specifications from a YAML file."""
    with Path(path).open(encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    contracts = payload.get("contracts", {}) if payload else {}
    if not isinstance(contracts, dict):
        raise ValueError("contracts must be a mapping")
    for symbol, specification in contracts.items():
        missing = REQUIRED_CONTRACT_KEYS - set(specification)
        if missing:
            raise ValueError(f"{symbol} is missing keys: {sorted(missing)}")
    return contracts
