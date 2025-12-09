"""Minimal serve module wrapper around aserpc.

This module provides:
- Model file discovery for local mode
- Re-exports from mlipx.aserpc (spawn configs, model extras)
- Re-exports useful aserpc functions

Examples
--------
Start the broker with on-demand worker spawning:

    $ mlipx serve-broker --autostart

Start workers manually:

    $ mlipx serve mace-mpa-0
    # or directly:
    $ aserpc worker mace-mpa-0

Use in Python (unified interface):

    >>> from mlipx import Models
    >>> models = Models()  # auto-detects serve vs local mode
    >>> list(models)
    ['mace-mpa-0', '7net-0']
    >>> calc = models['mace-mpa-0'].get_calculator()
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

if TYPE_CHECKING:
    from mlipx.abc import NodeWithCalculator

logger = logging.getLogger(__name__)

# Re-export from mlipx.aserpc
from mlipx.aserpc import MODEL_EXTRAS, _build_spawn_command

# Re-export useful aserpc functions
try:
    from aserpc import (
        Broker,
        RemoteCalculator,
        Worker,
        broker_status,
        list_calculators,
        shutdown_workers,
    )

    __all__ = [
        "Broker",
        "Worker",
        "RemoteCalculator",
        "broker_status",
        "list_calculators",
        "shutdown_workers",
        "discover_models_file",
        "load_models_from_file",
        "is_broker_running",
        "MODEL_EXTRAS",
        "get_model_extras",
        "build_worker_command",
    ]
except ImportError:
    __all__ = [
        "discover_models_file",
        "load_models_from_file",
        "is_broker_running",
        "MODEL_EXTRAS",
        "get_model_extras",
        "build_worker_command",
    ]


# ==============================================================================
# Model File Discovery (for local mode)
# ==============================================================================


def discover_models_file(
    explicit_path: Path | None = None,
    start_dir: Path | None = None,
) -> tuple[Path, str]:
    """Discover models.py file with upward search.

    Discovery order (highest to lowest priority):
    1. Explicit path (--models flag)
    2. MLIPX_MODELS environment variable
    3. Search upward for models.py containing ALL_MODELS
    4. Built-in package default (models.py.jinja2)

    Parameters
    ----------
    explicit_path : Path | None
        Explicit path to models file (from --models flag).
    start_dir : Path | None
        Directory to start upward search from. Defaults to cwd.

    Returns
    -------
    tuple[Path, str]
        (path, source) where source describes where it was found.

    Raises
    ------
    FileNotFoundError
        If explicit path or env var path doesn't exist.
    """
    # 1. Explicit path always wins
    if explicit_path is not None:
        if not explicit_path.exists():
            raise FileNotFoundError(f"Models file not found: {explicit_path}")
        return explicit_path, "explicit --models flag"

    # 2. Environment variable
    env_path = os.getenv("MLIPX_MODELS")
    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise FileNotFoundError(f"MLIPX_MODELS={env_path} does not exist")
        return path, "MLIPX_MODELS environment variable"

    # 3. Search upward for models.py
    found = _search_upward_for_models(start_dir or Path.cwd())
    if found:
        return found, f"discovered at {found.parent}"

    # 4. Built-in default
    from mlipx import recipes

    default = Path(recipes.__file__).parent / "models.py.jinja2"
    return default, "built-in package default"


def _search_upward_for_models(start: Path) -> Path | None:
    """Search upward for models.py containing ALL_MODELS."""
    current = start.resolve()

    while current != current.parent:
        candidate = current / "models.py"
        if candidate.exists() and _is_mlipx_models_file(candidate):
            return candidate
        current = current.parent

    return None


def _is_mlipx_models_file(path: Path) -> bool:
    """Check if file looks like an mlipx models file."""
    try:
        content = path.read_text()
        return "ALL_MODELS" in content
    except Exception:
        return False


def load_models_from_file(models_file: Path) -> dict[str, "NodeWithCalculator"]:
    """Load models from a models.py file.

    Parameters
    ----------
    models_file : Path
        Path to models.py file containing ALL_MODELS dict.

    Returns
    -------
    dict[str, NodeWithCalculator]
        Dictionary mapping model names to model nodes.
    """
    import mlipx

    if models_file.suffix == ".jinja2":
        # Render jinja2 template
        template = jinja2.Template(models_file.read_text())
        rendered_code = template.render(models=[])
    else:
        rendered_code = models_file.read_text()

    # Execute in namespace
    namespace = {"mlipx": mlipx}
    exec(rendered_code, namespace)

    # Get ALL_MODELS
    if "ALL_MODELS" not in namespace:
        raise ValueError(f"models file {models_file} must define ALL_MODELS dict")

    return namespace["ALL_MODELS"]  # type: ignore[return-value]


# ==============================================================================
# Broker Status
# ==============================================================================


def is_broker_running() -> bool:
    """Check if aserpc broker is running."""
    try:
        from aserpc import broker_status

        status = broker_status()
        return status is not None
    except Exception:
        return False


def get_model_extras(model_name: str) -> list[str]:
    """Get the extras required for a model.

    Parameters
    ----------
    model_name : str
        Name of the model.

    Returns
    -------
    list[str]
        List of extras required for the model.
    """
    return MODEL_EXTRAS.get(model_name, [])


def build_worker_command(
    model_name: str,
    model_extras: list[str],
    idle_timeout: int = 300,
    heartbeat: float = 5.0,
    log_level: str = "INFO",
) -> tuple[list[str], str]:
    """Build command to spawn an aserpc worker.

    Parameters
    ----------
    model_name : str
        Name of the model to serve.
    model_extras : list[str]
        Extras required for the model.
    idle_timeout : int
        Idle timeout in seconds.
    heartbeat : float
        Heartbeat interval in seconds.
    log_level : str
        Log level.

    Returns
    -------
    tuple[list[str], str]
        (command, method) where method describes the dependency resolution.
    """
    # Get base command from _build_spawn_command
    base_cmd = _build_spawn_command(model_name, model_extras)

    # Determine method based on command structure
    if base_cmd[0] == "uvx":
        method = "uvx (installing from mlipx package)"
    elif base_cmd[0] == "uv" and "--extra" in base_cmd:
        method = "uv run --extra (using local project extras)"
    else:
        method = "direct (no extras needed)"

    # Add worker options
    cmd = base_cmd + [
        "--idle-timeout",
        str(idle_timeout),
        "--heartbeat",
        str(heartbeat),
        "--log-level",
        log_level,
    ]

    return cmd, method


