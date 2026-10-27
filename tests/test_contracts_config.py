from pathlib import Path

from goldlens.ingest.contract_registry import REQUIRED_CONTRACT_KEYS, load_contracts


def test_contracts_config_loads() -> None:
    contracts = load_contracts(Path(__file__).parents[1] / "config" / "contracts.yml")
    assert set(contracts) == {"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"}
    assert all(REQUIRED_CONTRACT_KEYS <= set(spec) for spec in contracts.values())
