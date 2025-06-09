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
            "data.code": {
                "mace-mpa-0": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "data.method.functional": {
                "mace-mpa-0": "PBE+U",
                "pet-mad": "PBEsol",
            },
            "data.pseudopotential.name": {
                "mace-mpa-0": None,
                "pet-mad": "PBEsol",
            },
        },
    }

    assert compare_specs(
        {"mace-mpa-0": model_a, "pet-mad": model_b, "mattersim": model_c}
    ) == {
        ("mace-mpa-0", "mattersim"): {
            "data.basis_set.plane_wave_cutoff_eV": {
                "mace-mpa-0": None,
                "mattersim": 520.0,
            },
            "data.basis_set.type": {
                "mace-mpa-0": None,
                "mattersim": "plane-wave",
            },
        },
        ("mace-mpa-0", "pet-mad"): {
            "data.code": {
                "mace-mpa-0": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "data.method.functional": {
                "mace-mpa-0": "PBE+U",
                "pet-mad": "PBEsol",
            },
            "data.pseudopotential.name": {
                "mace-mpa-0": None,
                "pet-mad": "PBEsol",
            },
        },
        ("pet-mad", "mattersim"): {
            "data.basis_set.plane_wave_cutoff_eV": {
                "mattersim": 520.0,
                "pet-mad": None,
            },
            "data.basis_set.type": {
                "mattersim": "plane-wave",
                "pet-mad": None,
            },
            "data.code": {
                "mattersim": "VASP",
                "pet-mad": "QuantumEspresso",
            },
            "data.method.functional": {
                "mattersim": "PBE+U",
                "pet-mad": "PBEsol",
            },
            "data.pseudopotential.name": {
                "mattersim": None,
                "pet-mad": "PBEsol",
            },
        },
    }

    assert compare_specs({"a": model_a, "b": None}) == {
        ("a", "b"): {
            "data.code": {
                "a": "VASP",
                "b": None,
            },
            "data.method.functional": {
                "a": "PBE+U",
                "b": None,
            },
            "data.spin_polarized": {
                "a": False,
                "b": None,
            },
            "data.type": {
                "a": "DFT",
                "b": None,
            },
        },
    }
