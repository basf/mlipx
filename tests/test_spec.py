import importlib
from pathlib import Path

import pytest
import yaml

from mlipx.spec import MLIPS, compare_specs


@pytest.fixture(scope="module")
def mlipx_spec() -> MLIPS:
    """Load the MLIPX specification from the package."""
    # Import the mlipx package and load the spec file
    package = importlib.import_module("mlipx")
    base_path = Path(package.__path__[0])
    spec_path = base_path / "spec" / "mlips.yaml"
    # TODO: load via pydantic MLIPS class
    with spec_path.open("r") as f:
        mlip_spec = yaml.safe_load(f)
    return MLIPS.model_validate(mlip_spec)


def test_compare_specs(mlipx_spec):
    """Test the compare_specs function with the loaded MLIPX spec."""
    # Resolve datasets in the spec
    model_a = mlipx_spec.root["mace-mpa-0"]
    model_b = mlipx_spec.root["pet-mad"]
    model_c = mlipx_spec.root["mattersim"]

    assert compare_specs({"a": model_a, "b": model_a}) == {}

    assert compare_specs({"mace-mpa-0": model_a, "pet-mad": model_b}) == {
        ("mace-mpa-0", "pet-mad"): {
            "root['data']['code']": {
                "mace-mpa-0": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "root['data']['method']['functional']": {
                "mace-mpa-0": "PBE+U",
                "pet-mad": "PBEsol",
            },
        },
    }

    assert compare_specs(
        {"mace-mpa-0": model_a, "pet-mad": model_b, "mattersim": model_c}
    ) == {
        ("mace-mpa-0", "pet-mad"): {
            "root['data']['code']": {
                "mace-mpa-0": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "root['data']['method']['functional']": {
                "mace-mpa-0": "PBE+U",
                "pet-mad": "PBEsol",
            },
        },
        ("pet-mad", "mattersim"): {
            "root['data']['code']": {
                "mattersim": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "root['data']['method']['functional']": {
                "mattersim": "PBE+U",
                "pet-mad": "PBEsol",
            },
        },
    }
