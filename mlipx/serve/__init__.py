"""ZeroMQ-based server/client interface for MLIP calculations.

This module provides a broker-based architecture for serving MLIP models:

- Broker: Central routing process using LRU load balancing
- Workers: Model servers that perform calculations
- Clients: Connect via mlipx.Models to get calculators (unified local/serve interface)

Examples
--------
Start the broker:

    $ mlipx serve-broker

Start workers (in separate terminals):

    $ uv run --extra mace mlipx serve mace-mpa-0
    $ uv run --extra sevenn mlipx serve 7net-0

Use in Python (unified interface - works with or without serve mode):

    >>> from mlipx import Models
    >>> models = Models()  # auto-detects serve vs local mode
    >>> list(models)
    ['mace-mpa-0', '7net-0']
    >>> calc = models['mace-mpa-0'].get_calculator()
    >>> atoms.calc = calc
    >>> energy = atoms.get_potential_energy()

Note
----
This module requires the ``serve`` extra to be installed:

    pip install mlipx[serve]
"""

try:
    import msgpack  # noqa: F401
    import zmq  # noqa: F401
except ImportError as e:
    raise ImportError(
        "The serve module requires additional dependencies. "
        "Install with: pip install mlipx[serve]"
    ) from e

from .autostart_broker import AutoStartBroker, run_autostart_broker
from .broker import Broker, run_broker
from .client import (
    ModelProxy,
    RemoteCalculator,
    get_broker_detailed_status,
    get_broker_status,
    shutdown_broker,
)
from .command import build_serve_command
from .discovery import discover_models_file
from .protocol import get_default_broker_path, get_default_workers_path
from .worker import Worker, run_worker

__all__ = [
    # Client API (main user-facing interface)
    # Note: Models class moved to mlipx.Models for unified local/serve access
    "RemoteCalculator",
    "ModelProxy",
    "get_broker_status",
    "get_broker_detailed_status",
    "shutdown_broker",
    # Broker
    "Broker",
    "run_broker",
    "AutoStartBroker",
    "run_autostart_broker",
    # Worker
    "Worker",
    "run_worker",
    # Utilities
    "get_default_broker_path",
    "get_default_workers_path",
    "discover_models_file",
    "build_serve_command",
]
