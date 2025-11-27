"""Command building utilities for serve module.

This module provides utilities for building commands to start workers
with smart dependency resolution.
"""

import importlib.metadata
import pathlib


def _get_local_pyproject_extras() -> set[str]:
    """Get optional-dependencies (extras) from local pyproject.toml if it exists.

    Returns
    -------
    set[str]
        Set of extra names defined in the local pyproject.toml,
        or empty set if not found.
    """
    pyproject_path = pathlib.Path("pyproject.toml")
    if not pyproject_path.exists():
        return set()

    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        try:
            import tomli as tomllib
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
    """Build a package spec for uvx based on mlipx version.

    For release versions (e.g., "0.1.6"), uses PyPI with pinned version.
    For dev versions, uses the "Source Commit" URL from package metadata.

    Parameters
    ----------
    extras : list[str]
        List of extras to include (e.g., ["mace", "serve"]).

    Returns
    -------
    str
        Package specification for uvx --from.
    """
    import mlipx

    mlipx_version = mlipx.__version__
    extras_str = ",".join(extras)

    if mlipx_version and ("+" in mlipx_version or ".dev" in mlipx_version):
        # Dev version - get commit URL from package metadata
        metadata = importlib.metadata.metadata("mlipx")
        # Look for "Source Commit" URL which contains the commit hash
        for key, value in metadata.items():
            if key == "Project-URL" and value.startswith("Source Commit,"):
                # Format: "Source Commit, https://github.com/basf/mlipx/tree/abc123"
                url = value.split(", ", 1)[1]
                # Extract commit hash from URL
                commit_hash = url.rstrip("/").split("/")[-1]
                return (
                    f"mlipx[{extras_str}] @ "
                    f"git+https://github.com/basf/mlipx@{commit_hash}"
                )
        # No Source Commit URL found, use latest from PyPI
        return f"mlipx[{extras_str}]"
    elif mlipx_version:
        # Release version, use PyPI with pinned version
        return f"mlipx[{extras_str}]=={mlipx_version}"
    else:
        # No version available, use latest from PyPI
        return f"mlipx[{extras_str}]"


def build_serve_command(
    model_name: str,
    model_extras: list[str] | None,
    timeout: int = 300,
    broker: str | None = None,
    models_file: str | None = None,
) -> tuple[list[str], str]:
    """Build command to start a worker with smart dependency resolution.

    Checks if required extras exist in local pyproject.toml:
    - If yes: uses `uv run --extra`
    - If no: uses `uvx --from mlipx[extras,serve]`

    Parameters
    ----------
    model_name : str
        Name of the model to serve.
    model_extras : list[str] | None
        List of extras required by the model (e.g., ["mace"]).
    timeout : int
        Worker idle timeout in seconds.
    broker : str | None
        Custom broker backend path.
    models_file : str | None
        Path to models.py file.

    Returns
    -------
    tuple[list[str], str]
        Command list and a description of the resolution method used.
    """
    if model_extras:
        local_extras = _get_local_pyproject_extras()
        required_extras = set(model_extras)
        extras_str = ", ".join(sorted(required_extras))

        if required_extras.issubset(local_extras):
            # Use uv run --extra (extras available in local project)
            method = f"local extras [{extras_str}] via uv run --extra"
            cmd = ["uv", "run"]
            for dep in model_extras:
                cmd.extend(["--extra", dep])
            cmd.extend(["mlipx", "serve", model_name])
        else:
            # Use uvx --from mlipx[extras,serve] (extras from mlipx package)
            pkg_spec = _get_mlipx_package_spec(list(model_extras) + ["serve"])
            method = f"mlipx package extras [{extras_str}] via uvx ({pkg_spec})"
            cmd = ["uvx", "--from", pkg_spec, "mlipx", "serve", model_name]
    else:
        # No extras needed
        method = "no extras required"
        cmd = ["uv", "run", "mlipx", "serve", model_name]

    cmd.extend(["--timeout", str(timeout)])
    cmd.append("--no-uv")

    if broker:
        cmd.extend(["--broker", broker])
    if models_file:
        cmd.extend(["--models", str(models_file)])

    return cmd, method
