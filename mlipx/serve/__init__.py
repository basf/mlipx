"""ZeroMQ-based server/client interface for MLIP calculations.

This module provides a broker-based architecture for serving MLIP models:

- Broker: Central routing process using LRU load balancing
- Workers: Model servers that perform calculations
- Clients: Connect via the Models class to get RemoteCalculator instances

Examples
--------
Start the broker:

    $ mlipx serve-broker

Start workers (in separate terminals):

    $ uv run --extra mace mlipx serve mace-mpa-0
    $ uv run --extra sevenn mlipx serve 7net-0

Use in Python:

    >>> from mlipx.serve import Models
    >>> models = Models()
    >>> list(models)
    ['mace-mpa-0', '7net-0']
    >>> calc = models['mace-mpa-0'].get_calculator()
    >>> atoms.calc = calc
    >>> energy = atoms.get_potential_energy()
"""

from .broker import Broker, run_broker
from .client import (
    ModelProxy,
    Models,
    RemoteCalculator,
    get_broker_detailed_status,
    get_broker_status,
)
from .protocol import get_default_broker_path, get_default_workers_path
from .worker import Worker, run_worker

__all__ = [
    # Client API (main user-facing interface)
    "Models",
    "RemoteCalculator",
    "ModelProxy",
    "get_broker_status",
    "get_broker_detailed_status",
    # Broker
    "Broker",
    "run_broker",
    # Worker
    "Worker",
    "run_worker",
    # Utilities
    "get_default_broker_path",
    "get_default_workers_path",
]
