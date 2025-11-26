"""Model file discovery for mlipx serve."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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
    """Search upward for models.py containing ALL_MODELS.

    Parameters
    ----------
    start : Path
        Directory to start searching from.

    Returns
    -------
    Path | None
        Path to models.py if found, None otherwise.
    """
    current = start.resolve()

    while current != current.parent:
        candidate = current / "models.py"
        if candidate.exists() and _is_mlipx_models_file(candidate):
            return candidate
        current = current.parent

    return None


def _is_mlipx_models_file(path: Path) -> bool:
    """Check if file looks like an mlipx models file.

    A valid mlipx models file must contain 'ALL_MODELS'.

    Parameters
    ----------
    path : Path
        Path to check.

    Returns
    -------
    bool
        True if file contains ALL_MODELS.
    """
    try:
        content = path.read_text()
        return "ALL_MODELS" in content
    except Exception:
        return False
