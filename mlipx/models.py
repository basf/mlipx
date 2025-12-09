"""Unified interface for accessing MLIP models.

This module provides the `Models` class: a unified interface that works with
local files or serve mode (via aserpc).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from mlipx.serve import is_broker_running

if TYPE_CHECKING:
    from ase.calculators.calculator import Calculator

    from mlipx.abc import ModelProxy as ModelProxyProtocol
    from mlipx.abc import NodeWithCalculator

logger = logging.getLogger(__name__)


class LocalModelProxy:
    """Proxy for a locally-loaded model.

    Provides the same interface as the serve ModelProxy but executes locally.
    """

    def __init__(self, model_name: str, model: "NodeWithCalculator"):
        self.model_name = model_name
        self._model = model

    def get_calculator(self, **kwargs) -> "Calculator":
        """Get an ASE calculator for this model."""
        return self._model.get_calculator(**kwargs)

    def __repr__(self) -> str:
        return f"LocalModelProxy(model={self.model_name!r})"


class ServeModelProxy:
    """Proxy for a model served via aserpc.

    Provides the same interface as LocalModelProxy but uses aserpc.RemoteCalculator.
    """

    def __init__(self, model_name: str, timeout_ms: int | None = None):
        self.model_name = model_name
        self.timeout_ms = timeout_ms

    def get_calculator(self, **kwargs) -> "Calculator":
        """Get an aserpc RemoteCalculator for this model."""
        from aserpc import RemoteCalculator

        # Pass timeout if specified and not overridden
        if self.timeout_ms is not None and "timeout_ms" not in kwargs:
            kwargs["timeout_ms"] = self.timeout_ms
        return RemoteCalculator(self.model_name, **kwargs)

    def __repr__(self) -> str:
        return f"ServeModelProxy(model={self.model_name!r})"


class _ModelBackend(ABC):
    """Abstract backend for model access."""

    @abstractmethod
    def get_model_names(self) -> list[str]:
        """Return list of available model names."""

    @abstractmethod
    def get_proxy(self, key: str) -> "ModelProxyProtocol":
        """Return a proxy for the given model."""

    @abstractmethod
    def get_repr_info(self) -> str:
        """Return info string for repr."""


class _LocalBackend(_ModelBackend):
    """Backend for local model access."""

    def __init__(self, path: str | Path | None):
        self._models_path = self._resolve_path(path)
        self._models = self._load_models()

    def _resolve_path(self, path: str | Path | None) -> Path:
        from mlipx.serve import discover_models_file

        path_obj = Path(path) if isinstance(path, str) else path
        models_path, source = discover_models_file(explicit_path=path_obj)
        logger.debug(f"Using models file: {models_path} ({source})")
        return models_path

    def _load_models(self) -> dict[str, "NodeWithCalculator"]:
        from mlipx.serve import load_models_from_file

        return load_models_from_file(self._models_path)

    def get_model_names(self) -> list[str]:
        return list(self._models.keys())

    def get_proxy(self, key: str) -> LocalModelProxy:
        if key not in self._models:
            available = ", ".join(sorted(self._models.keys()))
            raise KeyError(f"Model '{key}' not found. Available: {available}")
        return LocalModelProxy(key, self._models[key])

    def get_repr_info(self) -> str:
        return f"mode='local', path={self._models_path}"

    @property
    def path(self) -> Path:
        return self._models_path


class _ServeBackend(_ModelBackend):
    """Backend for serve mode model access via aserpc."""

    def __init__(self, timeout: int | None):
        self._timeout = timeout  # timeout in milliseconds
        self._cached_models: list[str] | None = None

    def _fetch_models(self) -> list[str]:
        """Fetch available models from broker (includes spawnable models with 0 workers)."""
        from aserpc import list_calculators

        try:
            # list_calculators returns {model: worker_count}
            # With manager, spawnable models show with count=0
            calcs = list_calculators()
            return list(calcs.keys())
        except Exception as e:
            logger.warning(f"Failed to list calculators from broker: {e}")
            return []

    def get_model_names(self) -> list[str]:
        """Return available models (from broker, includes spawnable models)."""
        if self._cached_models is None:
            self._cached_models = self._fetch_models()
        return self._cached_models

    def refresh(self) -> None:
        """Clear the cached model list, forcing a fresh fetch on next access."""
        self._cached_models = None

    def get_proxy(self, key: str) -> ServeModelProxy:
        # With manager running, just return proxy - manager handles spawning
        return ServeModelProxy(key, timeout_ms=self._timeout)

    def get_repr_info(self) -> str:
        return "mode='serve'"


class Models(Mapping):
    """Unified interface for accessing MLIP models.

    Works seamlessly in two modes:
    - Local: Load models directly from models.py file
    - Serve: Connect to running aserpc broker for remote execution

    Mode is auto-detected based on broker availability, unless explicitly set.

    This class implements the Mapping protocol, allowing dict-like access:
    - `list(models)` - List available models
    - `len(models)` - Number of available models
    - `model_name in models` - Check if model is available
    - `models[model_name]` - Get a proxy for the model

    Examples
    --------
    >>> from mlipx import Models
    >>> models = Models()
    >>> list(models)
    ['mace-mpa-0', '7net-0', 'chgnet']
    >>> calc = models['mace-mpa-0'].get_calculator()
    >>> atoms.calc = calc
    >>> energy = atoms.get_potential_energy()

    Using with specific models (recipe pattern):
    >>> models = Models()
    >>> RECIPE_MODELS = ["mace-mpa-0", "orb-v2"]
    >>> for model_name in RECIPE_MODELS:
    ...     model = models[model_name]
    ...     calc = model.get_calculator()
    """

    def __init__(
        self,
        path: str | Path | None = None,
        timeout: int | None = None,
        local: bool | None = None,
    ):
        """Initialize the Models collection.

        Parameters
        ----------
        path : str | Path | None
            Path to models.py file (for local mode). If None, uses discovery
            (upward search). If just a filename (e.g., "models.py"), searches
            upward for it. If a path with directory (e.g., "./models.py"), uses as-is.
        timeout : int | None
            Timeout in milliseconds for serve mode. If None, uses aserpc defaults.
        local : bool | None
            Force local mode (True), force serve mode (False), or auto-detect (None).
            Auto-detect tries serve first if broker is available, falls back to local.
        """
        self._mode: Literal["local", "serve"]
        self._backend: _ModelBackend

        if local is True:
            self._mode = "local"
            self._backend = _LocalBackend(path)
        elif local is False:
            self._mode = "serve"
            self._backend = _ServeBackend(timeout)
        elif is_broker_running():
            self._mode = "serve"
            self._backend = _ServeBackend(timeout)
        else:
            self._mode = "local"
            self._backend = _LocalBackend(path)

    def __getitem__(self, key: str):
        """Get a model proxy for the given model name."""
        return self._backend.get_proxy(key)

    def __iter__(self):
        """Iterate over available model names."""
        return iter(self._backend.get_model_names())

    def __len__(self) -> int:
        """Return the number of available models."""
        return len(self._backend.get_model_names())

    def __contains__(self, key: object) -> bool:
        """Check if a model is available."""
        return key in self._backend.get_model_names()

    def __repr__(self) -> str:
        """Return detailed string representation."""
        try:
            models = self._backend.get_model_names()
            return f"Models({self._backend.get_repr_info()}, models={models})"
        except Exception as e:
            return f"Models({self._backend.get_repr_info()}, error={e})"

    def __str__(self) -> str:
        """Return concise string representation."""
        try:
            models = self._backend.get_model_names()
            model_str = ", ".join(models[:3])
            if len(models) > 3:
                model_str += f", ... ({len(models)} total)"
            return f"Models([{model_str}], mode='{self._mode}')"
        except Exception:
            return f"Models(mode='{self._mode}')"

    def refresh(self) -> None:
        """Refresh the model list (serve mode only).

        In serve mode, clears the cached model list so the next access
        fetches fresh data from the broker. In local mode, this is a no-op.
        """
        if isinstance(self._backend, _ServeBackend):
            self._backend.refresh()

    @property
    def mode(self) -> Literal["local", "serve"]:
        """Return current mode ('local' or 'serve')."""
        return self._mode

    @property
    def path(self) -> Path | None:
        """Return path to models.py file (local mode only)."""
        if isinstance(self._backend, _LocalBackend):
            return self._backend.path
        return None
