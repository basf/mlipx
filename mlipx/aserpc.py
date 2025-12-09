"""ASE RPC calculator and spawn config provider.

This module provides:
- Calculator metadata for the aserpc plugin system (aserpc.calculators entry point)
- Spawn configurations for on-demand worker spawning (aserpc.spawn entry point)

Uses importlib.util.find_spec() for lightweight package detection without
triggering expensive imports (like torch).

Register via entry points in pyproject.toml:
    [project.entry-points."aserpc.calculators"]
    mlipx = "mlipx.aserpc:get_calculators"

    [project.entry-points."aserpc.spawn"]
    mlipx = "mlipx.aserpc:get_spawn_configs"
"""

import importlib.metadata
import importlib.util
import pathlib


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

    return calcs


# Model name to extras mapping for spawn configurations
MODEL_EXTRAS: dict[str, list[str]] = {
    "mace-mpa-0": ["mace"],
    "7net-0": ["sevenn"],
    "7net-mf-ompa-mpa": ["sevenn"],
    "orb-v2": ["orb"],
    "orb-v3": ["orb"],
    "chgnet": ["chgnet"],
    "mattersim": ["mattersim"],
}


def _get_local_pyproject_extras() -> set[str]:
    """Get optional-dependencies (extras) from local pyproject.toml if it exists."""
    pyproject_path = pathlib.Path("pyproject.toml")
    if not pyproject_path.exists():
        return set()

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found]
        except ImportError:
            return set()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        return set(optional_deps.keys())
    except Exception:
        return set()


def _get_mlipx_package_spec(extras: list[str]) -> str:
    """Build a package spec for uvx based on mlipx version."""
    import mlipx

    mlipx_version = mlipx.__version__
    extras_str = ",".join(extras)

    if mlipx_version and ("+" in mlipx_version or ".dev" in mlipx_version):
        # Dev version - get commit URL from package metadata
        metadata = importlib.metadata.metadata("mlipx")
        project_urls = metadata.get_all("Project-URL") or []
        for url_entry in project_urls:
            if url_entry.startswith("Source Commit,"):
                url = url_entry.split(", ", 1)[1]
                commit_hash = url.rstrip("/").split("/")[-1]
                return (
                    f"mlipx[{extras_str}] @ "
                    f"git+https://github.com/basf/mlipx@{commit_hash}"
                )
        return f"mlipx[{extras_str}]"
    elif mlipx_version:
        return f"mlipx[{extras_str}]=={mlipx_version}"
    else:
        return f"mlipx[{extras_str}]"


def _build_spawn_command(model_name: str, extras: list[str]) -> list[str]:
    """Build command to spawn a worker with smart dependency resolution.

    Resolution order:
    1. If extras exist in local pyproject.toml → uv run --extra (custom models)
    2. If model is known to mlipx (in MODEL_EXTRAS) → uvx --from mlipx[extras]
    3. If no extras needed → plain aserpc worker
    4. Otherwise → raise error (unknown model with unknown extras)
    """
    if not extras:
        # No extras needed - just run aserpc worker
        return ["aserpc", "worker", model_name]

    local_extras = _get_local_pyproject_extras()
    required_extras = set(extras)

    if required_extras.issubset(local_extras):
        # Use uv run --extra (extras available in local project - custom models)
        cmd = ["uv", "run"]
        for dep in extras:
            cmd.extend(["--extra", dep])
        cmd.extend(["aserpc", "worker", model_name])
        return cmd

    if model_name in MODEL_EXTRAS:
        # Known mlipx model - use uvx --from mlipx[extras]
        pkg_spec = _get_mlipx_package_spec(extras)
        return ["uvx", "--from", pkg_spec, "aserpc", "worker", model_name]

    # Unknown model with extras not in local pyproject.toml
    raise ValueError(
        f"Model '{model_name}' requires extras {extras} but they are not found in "
        f"local pyproject.toml and '{model_name}' is not a known mlipx model. "
        f"Either add the extras to your pyproject.toml or use a known model: "
        f"{list(MODEL_EXTRAS.keys())}"
    )


def get_spawn_configs() -> dict:
    """Return spawn configurations for on-demand worker spawning.

    This is used by aserpc's Manager to spawn workers on demand.
    Each config specifies how to spawn a worker for a given model.
    """
    from aserpc.spawn import SpawnConfig

    configs = {}

    for model_name, extras in MODEL_EXTRAS.items():
        cmd = _build_spawn_command(model_name, extras)
        configs[model_name] = SpawnConfig(
            name=model_name,
            command=cmd,
            idle_timeout=300.0,
        )

    return configs
