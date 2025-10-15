"""Worker process that serves MLIP calculations via ZeroMQ."""

import logging
import os
import secrets
import signal
import socket
import sys
import time
from pathlib import Path

import jinja2
import zmq

import mlipx
from mlipx.abc import NodeWithCalculator

from .protocol import (
    HEARTBEAT,
    READY,
    check_broker_socket_exists,
    get_default_workers_path,
    pack_response,
    unpack_request,
)

logger = logging.getLogger(__name__)

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 5.0


class Worker:
    """ZeroMQ worker that serves MLIP calculations.

    Workers connect to the broker backend using DEALER sockets.
    They signal availability by sending READY messages and process
    calculation requests from the broker.
    """

    def __init__(
        self,
        model_name: str,
        model_node: NodeWithCalculator,
        backend_path: str | None = None,
        timeout: int = 300,
    ):
        """Initialize the worker.

        Parameters
        ----------
        model_name : str
            Name of the model being served.
        model_node : NodeWithCalculator
            Node that provides get_calculator() method.
        backend_path : str | None
            IPC path to connect to broker backend.
        timeout : int
            Idle timeout in seconds. Worker will shut down after this
            period of inactivity. Default is 300 seconds (5 minutes).
            Timeout resets with every calculation request.
        """
        self.model_name = model_name
        self.model_node = model_node
        self.backend_path = backend_path or get_default_workers_path()
        self.timeout = timeout

        # Generate a unique worker identity with hostname and random suffix
        # to prevent collisions across machines or PID reuse
        hostname = socket.gethostname()
        pid = os.getpid()
        random_suffix = secrets.token_hex(4)
        self.worker_id = f"worker-{model_name}-{hostname}-{pid}-{random_suffix}".encode(
            "utf-8"
        )

        # Calculator will be loaded on demand
        self.calculator = None

        # ZeroMQ context and socket
        self.ctx: zmq.Context | None = None
        self.socket: zmq.Socket | None = None

        # Heartbeat tracking
        self.last_heartbeat = 0.0

        # Timeout tracking - reset on every request
        self.last_request_time = 0.0

        # Signal handling for graceful shutdown
        self.running = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _load_calculator(self):
        """Load the calculator (expensive operation, done once)."""
        if self.calculator is None:
            logger.info(f"Loading calculator for model '{self.model_name}'...")
            try:
                self.calculator = self.model_node.get_calculator()
                logger.info(f"Calculator loaded successfully for '{self.model_name}'")
            except Exception as e:
                logger.error(f"Failed to load calculator: {e}")
                raise

    def start(self):
        """Start the worker and begin processing requests."""
        self.running = True

        # Check if broker socket exists
        if not check_broker_socket_exists(self.backend_path):
            logger.error(
                f"Broker socket not found at {self.backend_path}. "
                "Is the broker running? Start it with: mlipx serve-broker"
            )
            raise RuntimeError(
                f"Broker socket not found at {self.backend_path}. "
                "Make sure the broker is running before starting workers."
            )

        # Load calculator before connecting
        self._load_calculator()

        # Initialize ZeroMQ
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.DEALER)
        # Set the identity for readable worker names
        self.socket.setsockopt(zmq.IDENTITY, self.worker_id)
        self.socket.connect(self.backend_path)
        logger.info(
            f"Worker {self.worker_id.decode('utf-8')} connected to broker at {self.backend_path}"
        )

        # Send initial READY message
        self._send_ready()
        self.last_heartbeat = time.time()
        self.last_request_time = time.time()
        logger.info(
            f"Worker {self.worker_id.decode('utf-8')} ready to serve model '{self.model_name}' "
            f"(timeout: {self.timeout}s)"
        )

        # Event loop
        while self.running:
            try:
                # Check for timeout
                if time.time() - self.last_request_time > self.timeout:
                    logger.info(
                        f"Worker timeout reached ({self.timeout}s idle), shutting down"
                    )
                    self.running = False
                    break

                # Send heartbeat if needed
                if time.time() - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                    self._send_heartbeat()

                # Wait for request with timeout (shorter to allow heartbeats)
                if self.socket.poll(timeout=1000):  # 1 second timeout
                    self._handle_request()
            except zmq.ZMQError as e:
                if self.running:  # Only log if not shutting down
                    # Check if broker disconnected
                    if e.errno in (
                        zmq.ETERM,
                        zmq.ENOTSOCK,
                        zmq.EHOSTUNREACH,
                    ) or not check_broker_socket_exists(self.backend_path):
                        logger.error(
                            f"Lost connection to broker at {self.backend_path}. "
                            "Broker may have shut down. Worker will exit."
                        )
                    else:
                        logger.error(f"ZMQ error: {e}")
                    break

        self.stop()

    def _send_ready(self):
        """Send READY message to broker."""
        # READY format: [b"", READY, model_name]
        self.socket.send_multipart([b"", READY, self.model_name.encode("utf-8")])

    def _send_heartbeat(self):
        """Send HEARTBEAT message to broker."""
        # HEARTBEAT format: [b"", HEARTBEAT, model_name]
        self.socket.send_multipart([b"", HEARTBEAT, self.model_name.encode("utf-8")])
        self.last_heartbeat = time.time()
        logger.debug(f"Worker {self.worker_id.decode('utf-8')} sent heartbeat")

    def _handle_request(self):
        """Handle a calculation request from the broker."""
        # Reset timeout on every request
        self.last_request_time = time.time()

        # Request format: [b"", client_id, b"", model_name, request_data]
        parts = self.socket.recv_multipart()

        if len(parts) < 5:
            logger.warning(f"Invalid request format: {parts}")
            self._send_ready()
            return

        client_id = parts[1]
        request_data = parts[4]

        try:
            # Unpack request
            atoms, properties = unpack_request(request_data)

            # Perform calculation
            atoms.calc = self.calculator
            response_dict = {"success": True}

            energy = None
            forces = None
            stress = None

            if "energy" in properties:
                energy = atoms.get_potential_energy()
                response_dict["energy"] = float(energy)

            if "forces" in properties:
                forces = atoms.get_forces()

            if "stress" in properties:
                stress = atoms.get_stress()

            # Pack response
            response_data = pack_response(
                success=True, energy=energy, forces=forces, stress=stress
            )

            logger.debug(
                f"Completed calculation for {len(atoms)} atoms, properties: {properties}"
            )

        except Exception as e:
            logger.error(f"Calculation failed: {e}", exc_info=True)
            response_data = pack_response(success=False, error=str(e))

        # Send response back to broker: [b"", client_id, b"", response_data]
        self.socket.send_multipart([b"", client_id, b"", response_data])

        # Signal ready for next task
        self._send_ready()

    def stop(self):
        """Stop the worker and clean up resources."""
        logger.info("Stopping worker...")

        if self.socket:
            self.socket.close()
        if self.ctx:
            self.ctx.term()

        logger.info("Worker stopped")


def load_models_from_file(models_file: Path) -> dict[str, NodeWithCalculator]:
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

    return namespace["ALL_MODELS"]


def run_worker(
    model_name: str,
    backend_path: str | None = None,
    models_file: Path | None = None,
    timeout: int = 300,
):
    """Run a worker process.

    Parameters
    ----------
    model_name : str
        Name of the model to serve (must exist in ALL_MODELS).
    backend_path : str | None
        IPC path to connect to broker backend.
    models_file : Path | None
        Path to models.py file. Defaults to mlipx/recipes/models.py.jinja2.
    timeout : int
        Idle timeout in seconds. Worker will shut down after this
        period of inactivity. Default is 300 seconds (5 minutes).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load models
    if models_file is None:
        from mlipx import recipes

        models_file = Path(recipes.__file__).parent / "models.py.jinja2"

    logger.info(f"Loading models from {models_file}")
    all_models = load_models_from_file(models_file)

    if model_name not in all_models:
        logger.error(f"Model '{model_name}' not found in {models_file}")
        logger.error(f"Available models: {list(all_models.keys())}")
        sys.exit(1)

    model_node = all_models[model_name]

    # Start worker
    worker = Worker(
        model_name=model_name,
        model_node=model_node,
        backend_path=backend_path,
        timeout=timeout,
    )

    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        worker.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m mlipx.serve.worker <model_name>")
        sys.exit(1)

    run_worker(sys.argv[1])
