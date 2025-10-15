"""Client interface for connecting to MLIP servers via ZeroMQ broker."""

import logging
from collections.abc import Mapping

import msgpack
import zmq
from ase import Atoms
from ase.calculators.calculator import Calculator

from .protocol import (
    LIST_MODELS,
    get_default_broker_path,
    pack_request,
    unpack_response,
)

logger = logging.getLogger(__name__)


class RemoteCalculator(Calculator):
    """ASE Calculator that communicates with remote MLIP workers via broker.

    This calculator connects to a ZeroMQ broker that routes requests to
    available workers using LRU load balancing.
    """

    implemented_properties = ["energy", "forces", "stress"]

    def __init__(
        self,
        model: str,
        broker: str | None = None,
        timeout: int = 30000,
        **kwargs,
    ):
        """Initialize the remote calculator.

        Parameters
        ----------
        model : str
            Name of the model to use.
        broker : str | None
            IPC path to broker. Defaults to platform-specific path.
        timeout : int
            Timeout in milliseconds for receiving responses. Default: 30000 (30s).
        **kwargs
            Additional arguments passed to Calculator base class.
        """
        super().__init__(**kwargs)
        self.model = model
        self.broker_path = broker or get_default_broker_path()
        self.timeout = timeout

        # ZeroMQ context and socket (created on demand)
        self._ctx: zmq.Context | None = None
        self._socket: zmq.Socket | None = None

    def _ensure_connected(self):
        """Ensure we have an active connection to the broker."""
        if self._ctx is None:
            self._ctx = zmq.Context()

        if self._socket is None:
            self._socket = self._ctx.socket(zmq.REQ)
            self._socket.setsockopt(zmq.RCVTIMEO, self.timeout)
            self._socket.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second send timeout
            self._socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
            self._socket.connect(self.broker_path)
            logger.debug(f"Connected to broker at {self.broker_path}")

    def _close_connection(self):
        """Close the connection to the broker."""
        if self._socket:
            self._socket.close()
            self._socket = None
        if self._ctx:
            self._ctx.term()
            self._ctx = None

    def calculate(
        self,
        atoms: Atoms | None = None,
        properties: list[str] | None = None,
        system_changes: list[str] | None = None,
    ):
        """Perform calculation by sending request to remote worker via broker.

        Parameters
        ----------
        atoms : Atoms | None
            Atoms object to calculate properties for.
        properties : list[str] | None
            Properties to calculate. Defaults to ['energy', 'forces'].
        system_changes : list[str] | None
            List of changes since last calculation.
        """
        if properties is None:
            properties = ["energy", "forces"]

        Calculator.calculate(self, atoms, properties, system_changes)

        if atoms is None:
            atoms = self.atoms

        # Pack request
        request_data = pack_request(atoms, properties=properties)

        # Send request to broker
        self._ensure_connected()

        try:
            # Request format: [model_name, request_data]
            self._socket.send_multipart([self.model.encode("utf-8"), request_data])

            # Receive response from broker
            response_data = self._socket.recv()
            response = unpack_response(response_data)

        except zmq.error.Again:
            # Timeout - need to recreate socket
            logger.error(
                f"Timeout waiting for response from broker (model: {self.model})"
            )
            self._close_connection()
            raise RuntimeError(
                f"Timeout waiting for response from broker. "
                f"Is the broker running? Are there workers for model '{self.model}'?"
            )

        except zmq.error.ZMQError as e:
            logger.error(f"ZMQ error: {e}")
            self._close_connection()
            raise RuntimeError(f"Communication error with broker: {e}")

        # Check if calculation succeeded
        if not response.get("success", False):
            error = response.get("error", "Unknown error")
            raise RuntimeError(f"Remote calculation failed: {error}")

        # Store results
        self.results = {}
        if "energy" in response:
            self.results["energy"] = response["energy"]
        if "forces" in response:
            self.results["forces"] = response["forces"]
        if "stress" in response:
            self.results["stress"] = response["stress"]

    def __del__(self):
        """Clean up connection when calculator is destroyed."""
        self._close_connection()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"RemoteCalculator(model={self.model!r}, broker={self.broker_path!r})"


class ModelProxy:
    """Proxy for a specific model available through the broker.

    This class provides a simple interface to get a calculator for a model.
    """

    def __init__(self, model_name: str, broker_path: str):
        """Initialize the model proxy.

        Parameters
        ----------
        model_name : str
            Name of the model.
        broker_path : str
            IPC path to the broker.
        """
        self.model_name = model_name
        self.broker_path = broker_path

    def get_calculator(self, **kwargs) -> RemoteCalculator:
        """Get a RemoteCalculator for this model.

        Parameters
        ----------
        **kwargs
            Additional arguments passed to RemoteCalculator.

        Returns
        -------
        RemoteCalculator
            Calculator that communicates with remote workers.
        """
        return RemoteCalculator(
            model=self.model_name, broker=self.broker_path, **kwargs
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ModelProxy(model={self.model_name!r})"


class Models(Mapping):
    """Collection interface to discover and connect to running model servers.

    This class implements the Mapping protocol, allowing dict-like access to models:
    - `list(models)` - List available models
    - `len(models)` - Number of available models
    - `model_name in models` - Check if model is available
    - `models[model_name]` - Get a ModelProxy for the model

    Examples
    --------
    >>> from mlipx.serve import Models
    >>> models = Models()
    >>> list(models)
    ['mace-mpa-0', '7net-0', 'chgnet']
    >>> calc = models['mace-mpa-0'].get_calculator()
    >>> atoms.calc = calc
    >>> energy = atoms.get_potential_energy()
    """

    def __init__(self, broker: str | None = None):
        """Initialize the Models collection.

        Parameters
        ----------
        broker : str | None
            IPC path to broker. Defaults to platform-specific path.
        """
        self.broker_path = broker or get_default_broker_path()

    def _fetch_models(self) -> list[str]:
        """Fetch the list of available models from the broker.

        Returns
        -------
        list[str]
            List of model names.
        """
        ctx = zmq.Context()
        socket = ctx.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        socket.setsockopt(zmq.SNDTIMEO, 5000)
        socket.setsockopt(zmq.LINGER, 0)

        try:
            socket.connect(self.broker_path)
            # REQ socket adds empty delimiter automatically, so just send LIST_MODELS
            socket.send_multipart([LIST_MODELS])
            response_data = socket.recv()
            response = msgpack.unpackb(response_data)
            return response.get("models", [])

        except zmq.error.Again:
            raise RuntimeError(
                f"Timeout connecting to broker at {self.broker_path}. "
                "Is the broker running?"
            )
        except zmq.error.ZMQError as e:
            raise RuntimeError(f"Failed to connect to broker: {e}")
        finally:
            socket.close()
            ctx.term()

    def _get_models(self) -> list[str]:
        """Get the list of models from the broker.

        Returns
        -------
        list[str]
            List of model names.

        Notes
        -----
        Always fetches fresh data from the broker. This is fast for local IPC
        and ensures the model list is always up-to-date.
        """
        return self._fetch_models()

    def __getitem__(self, key: str) -> ModelProxy:
        """Get a ModelProxy for the given model name.

        Parameters
        ----------
        key : str
            Model name.

        Returns
        -------
        ModelProxy
            Proxy for the model.

        Raises
        ------
        KeyError
            If the model is not available.
        """
        if key not in self._get_models():
            raise KeyError(
                f"Model '{key}' not available. Available models: {self._get_models()}"
            )
        return ModelProxy(key, self.broker_path)

    def __iter__(self):
        """Iterate over available model names."""
        return iter(self._get_models())

    def __len__(self) -> int:
        """Return the number of available models."""
        return len(self._get_models())

    def __repr__(self) -> str:
        """Return string representation."""
        try:
            models = self._get_models()
            return f"Models({models})"
        except Exception:
            return f"Models(broker={self.broker_path!r})"


def get_broker_status(broker_path: str | None = None) -> dict:
    """Get status information from the broker.

    Parameters
    ----------
    broker_path : str | None
        IPC path to broker. Defaults to platform-specific path.

    Returns
    -------
    dict
        Status information with keys:
        - broker_running: bool
        - broker_path: str
        - models: list[str]
        - error: str (if any)
    """
    from .protocol import get_default_broker_path

    broker_path = broker_path or get_default_broker_path()

    status = {
        "broker_running": False,
        "broker_path": broker_path,
        "models": [],
        "error": None,
    }

    try:
        models = Models(broker=broker_path)
        model_list = list(models)
        status["broker_running"] = True
        status["models"] = model_list
    except RuntimeError as e:
        status["error"] = str(e)
    except Exception as e:
        status["error"] = f"Unexpected error: {e}"

    return status
