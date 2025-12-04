"""ASE RPC calculator metadata provider.

This module provides calculator metadata for the aserpc plugin system.
Uses importlib.util.find_spec() for lightweight package detection without
triggering expensive imports (like torch).

Register via entry point in pyproject.toml:
    [project.entry-points."aserpc.calculators"]
    mlipx = "mlipx.aserpc:get_calculators"
"""

import importlib.util


def _create_orb_calculator(name: str = "orb_v2", device: str = "auto"):
    """Wrapper for ORB models that need pretrained loading."""
    from orb_models.forcefield import pretrained
    from orb_models.forcefield.calculator import ORBCalculator

    method = getattr(pretrained, name)
    if device == "auto":
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
    orbff = method(device=device)
    return ORBCalculator(orbff, device=device)


def _create_matgl_calculator(path: str):
    """Wrapper for matgl models that need load_model first."""
    import matgl
    from matgl.ext.ase import PESCalculator

    potential = matgl.load_model(path)
    return PESCalculator(potential)


def _create_fairchem_calculator(
    path: str, task_name: str = "oc20", device: str = "auto"
):
    """Wrapper for fairchem models."""
    from fairchem.core import FAIRChemCalculator
    from fairchem.core.units.mlip_unit import load_predict_unit

    if device == "auto":
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
    predictor = load_predict_unit(path, device=device)
    return FAIRChemCalculator(predictor, task_name=task_name)


def get_calculators() -> dict[str, dict]:
    """Return metadata for available calculators.

    Each entry is: {"factory": "module:class", "kwargs": {...}}
    or {"factory_fn": callable, "kwargs": {...}} for custom initialization.

    Uses importlib.util.find_spec() to check availability without importing.
    """
    calcs = {}

    # MACE models
    if importlib.util.find_spec("mace") is not None:
        calcs["mace-mpa-0"] = {
            "factory": "mace.calculators:mace_mp",
            "kwargs": {"model": "../../models/mace-mpa-0-medium.model"},
        }
        calcs["mace-matpes-pbe-0"] = {
            "factory": "mace.calculators:mace_mp",
            "kwargs": {"model": "../../models/mace-matpes-pbe-omat-ft.model"},
        }

    # SevenNet models
    if importlib.util.find_spec("sevenn") is not None:
        calcs["7net-0"] = {
            "factory": "sevenn.sevennet_calculator:SevenNetCalculator",
            "kwargs": {"model": "7net-0"},
        }
        calcs["7net-mf-ompa-mpa"] = {
            "factory": "sevenn.sevennet_calculator:SevenNetCalculator",
            "kwargs": {"model": "7net-mf-ompa", "modal": "mpa"},
        }

    # ORB models (custom init)
    if importlib.util.find_spec("orb_models") is not None:
        calcs["orb-v2"] = {
            "factory_fn": _create_orb_calculator,
            "kwargs": {"name": "orb_v2"},
        }
        calcs["orb-v3"] = {
            "factory_fn": _create_orb_calculator,
            "kwargs": {"name": "orb_v3_conservative_inf_omat"},
        }

    # CHGNet
    if importlib.util.find_spec("chgnet") is not None:
        calcs["chgnet"] = {"factory": "chgnet.model:CHGNetCalculator"}

    # MatterSim
    if importlib.util.find_spec("mattersim") is not None:
        calcs["mattersim"] = {
            "factory": "mattersim.forcefield:MatterSimCalculator",
        }

    # GRACE (tensorpotential)
    if importlib.util.find_spec("tensorpotential") is not None:
        calcs["grace-2l-omat"] = {
            "factory": "tensorpotential.calculator:TPCalculator",
            "kwargs": {"model": "../../models/GRACE-2L-OMAT"},
        }

    # MatGL models (custom init)
    if importlib.util.find_spec("matgl") is not None:
        calcs["matpes-pbe"] = {
            "factory_fn": _create_matgl_calculator,
            "kwargs": {"path": "../../models/TensorNet-MatPES-PBE-v2025.1-PES"},
        }

    # FairChem models (custom init)
    if importlib.util.find_spec("fairchem") is not None:
        calcs["meta-uma-sm"] = {
            "factory_fn": _create_fairchem_calculator,
            "kwargs": {"path": "../../models/meta-uam.pt"},
        }

    # PET-MAD
    if importlib.util.find_spec("pet_mad") is not None:
        calcs["pet-mad"] = {
            "factory": "pet_mad.calculator:PETMADCalculator",
            "kwargs": {"checkpoint_path": "../../models/pet-mad-latest.ckpt"},
        }

    return calcs
