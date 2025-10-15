"""Broker process for load balancing MLIP workers using the LRU pattern."""

import logging
import signal
import time
from collections import defaultdict, deque
from pathlib import Path

import msgpack
import zmq

from .protocol import (
    HEARTBEAT,
    LIST_MODELS,
    READY,
    get_default_broker_path,
    get_default_workers_path,
)

logger = logging.getLogger(__name__)

# Worker timeout in seconds - if no heartbeat received in this time, consider worker dead
WORKER_TIMEOUT = 15.0


class Broker:
    """ZeroMQ broker that implements LRU (Least Recently Used) load balancing.

    The broker uses two ROUTER sockets:
    - Frontend: receives requests from clients (REQ sockets)
    - Backend: communicates with workers (DEALER sockets)

    Workers register by sending READY messages with their model name.
    The broker maintains an LRU queue per model to ensure fair load distribution.
    """

    def __init__(
        self, frontend_path: str | None = None, backend_path: str | None = None
    ):
        """Initialize the broker.

        Parameters
        ----------
        frontend_path : str | None
            IPC path for client connections. Defaults to platform-specific path.
        backend_path : str | None
            IPC path for worker connections. Defaults to platform-specific path.
        """
        self.frontend_path = frontend_path or get_default_broker_path()
        self.backend_path = backend_path or get_default_workers_path()

        # LRU queue per model: {model_name: deque([worker_id, ...])}
        self.worker_queue: dict[str, deque[bytes]] = defaultdict(deque)

        # Track which model each worker serves: {worker_id: model_name}
        self.worker_model: dict[bytes, str] = {}

        # Track last heartbeat time for each worker: {worker_id: timestamp}
        self.worker_heartbeat: dict[bytes, float] = {}

        # ZeroMQ context and sockets
        self.ctx: zmq.Context | None = None
        self.frontend: zmq.Socket | None = None
        self.backend: zmq.Socket | None = None

        # Signal handling for graceful shutdown
        self.running = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _ensure_socket_dir(self, path: str):
        """Ensure the directory for the socket exists."""
        # Extract path from ipc:// URL
        if path.startswith("ipc://"):
            socket_path = path[6:]  # Remove 'ipc://'
            socket_dir = Path(socket_path).parent
            socket_dir.mkdir(parents=True, exist_ok=True)

    def _get_socket_path(self, path: str) -> Path | None:
        """Extract the filesystem path from an IPC URL."""
        if path.startswith("ipc://"):
            return Path(path[6:])
        return None

    def _cleanup_socket_files(self):
        """Remove IPC socket files on shutdown."""
        for path in [self.frontend_path, self.backend_path]:
            socket_path = self._get_socket_path(path)
            if socket_path and socket_path.exists():
                try:
                    socket_path.unlink()
                    logger.debug(f"Cleaned up socket file: {socket_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup socket {socket_path}: {e}")

    def start(self):
        """Start the broker and begin processing messages."""
        self.running = True

        # Ensure socket directories exist
        self._ensure_socket_dir(self.frontend_path)
        self._ensure_socket_dir(self.backend_path)

        # Clean up any stale socket files from previous unclean shutdown
        self._cleanup_socket_files()

        # Initialize ZeroMQ context and sockets
        self.ctx = zmq.Context()

        # Frontend socket for clients
        self.frontend = self.ctx.socket(zmq.ROUTER)
        self.frontend.bind(self.frontend_path)
        logger.info(f"Broker frontend listening on {self.frontend_path}")

        # Backend socket for workers
        self.backend = self.ctx.socket(zmq.ROUTER)
        self.backend.bind(self.backend_path)
        logger.info(f"Broker backend listening on {self.backend_path}")

        # Poller for both sockets
        poller = zmq.Poller()
        poller.register(self.backend, zmq.POLLIN)
        poller.register(self.frontend, zmq.POLLIN)

        logger.info("Broker started, ready to route messages")

        while self.running:
            try:
                socks = dict(poller.poll(timeout=1000))  # 1 second timeout

                # Handle worker messages (backend)
                if self.backend in socks:
                    self._handle_backend()

                # Handle client messages (frontend)
                if self.frontend in socks:
                    self._handle_frontend()

                # Periodically check for stale workers
                self._check_worker_health()

            except zmq.ZMQError as e:
                if self.running:  # Only log if not shutting down
                    logger.error(f"ZMQ error: {e}")

        self.stop()

    def _handle_backend(self):
        """Handle messages from workers."""
        # Worker message format:
        # [worker_id, b"", message_type, ...]
        parts = self.backend.recv_multipart()
        worker_id = parts[0]

        if len(parts) < 3:
            logger.warning(f"Invalid message from worker {worker_id}: {parts}")
            return

        message_type = parts[2]

        if message_type == READY:
            # READY message: [worker_id, b"", READY, model_name]
            if len(parts) < 4:
                logger.warning(f"Invalid READY message from worker {worker_id}")
                return

            model_name = parts[3].decode("utf-8")
            self._register_worker(worker_id, model_name)

        elif message_type == HEARTBEAT:
            # HEARTBEAT message: [worker_id, b"", HEARTBEAT, model_name]
            if len(parts) < 4:
                logger.warning(f"Invalid HEARTBEAT message from worker {worker_id}")
                return

            # Update heartbeat timestamp
            self.worker_heartbeat[worker_id] = time.time()
            logger.debug(
                f"Received heartbeat from worker {worker_id.decode('utf-8', errors='replace')}"
            )

        else:
            # Response message: [worker_id, b"", client_id, b"", response_data]
            if len(parts) < 5:
                logger.warning(f"Invalid response from worker {worker_id}: {parts}")
                return

            client_id = parts[2]
            response_data = parts[4]

            # Forward response to client
            self.frontend.send_multipart([client_id, b"", response_data])
            logger.debug(
                f"Routed response from worker {worker_id.decode('utf-8', errors='replace')} to client {client_id}"
            )

    def _handle_frontend(self):
        """Handle messages from clients."""
        # Client message format:
        # [client_id, b"", model_name, request_data] - for calculation requests
        # [client_id, b"", LIST_MODELS] - for model list requests
        parts = self.frontend.recv_multipart()

        if len(parts) < 3:
            logger.warning(f"Invalid message from client: {parts}")
            return

        client_id = parts[0]
        message_type = parts[2]

        if message_type == LIST_MODELS:
            # Return list of available models
            models = list(self.worker_queue.keys())
            response = msgpack.packb({"models": models})
            self.frontend.send_multipart([client_id, b"", response])
            logger.debug(f"Sent model list to client {client_id}: {models}")

        else:
            # Regular calculation request
            if len(parts) < 4:
                logger.warning(f"Invalid calculation request from client: {parts}")
                return

            model_name = message_type.decode("utf-8")
            request_data = parts[3]

            # Check if model has available workers
            if model_name not in self.worker_queue or not self.worker_queue[model_name]:
                error_response = msgpack.packb(
                    {
                        "success": False,
                        "error": f"No workers available for model '{model_name}'",
                    }
                )
                self.frontend.send_multipart([client_id, b"", error_response])
                logger.warning(f"No workers available for model '{model_name}'")
                return

            # Get LRU worker for this model
            worker_id = self.worker_queue[model_name].popleft()

            # Route request to worker: [worker_id, b"", client_id, b"", model_name, request_data]
            self.backend.send_multipart(
                [
                    worker_id,
                    b"",
                    client_id,
                    b"",
                    model_name.encode("utf-8"),
                    request_data,
                ]
            )
            logger.debug(
                f"Routed request from client {client_id} to worker {worker_id} (model: {model_name})"
            )

    def _register_worker(self, worker_id: bytes, model_name: str):
        """Register a worker as ready for the given model.

        Parameters
        ----------
        worker_id : bytes
            Unique worker identifier.
        model_name : str
            Name of the model this worker serves.
        """
        worker_name = worker_id.decode("utf-8", errors="replace")

        # Check if this is truly a new worker (first time seeing it)
        is_new_worker = worker_id not in self.worker_model

        # Update worker tracking
        old_model = self.worker_model.get(worker_id)
        if old_model and old_model != model_name:
            # Worker changed models (shouldn't happen, but handle it)
            if worker_id in self.worker_queue[old_model]:
                self.worker_queue[old_model].remove(worker_id)

        self.worker_model[worker_id] = model_name
        self.worker_heartbeat[worker_id] = time.time()

        # Add to LRU queue for this model
        # Note: Worker might not be in queue if it was popped to handle a request
        if worker_id not in self.worker_queue[model_name]:
            self.worker_queue[model_name].append(worker_id)
            if is_new_worker:
                logger.info(
                    f"New worker {worker_name} registered for model '{model_name}'"
                )
            else:
                logger.debug(f"Worker {worker_name} ready for model '{model_name}'")

    def _check_worker_health(self):
        """Check for stale workers and remove them."""
        current_time = time.time()
        stale_workers = []

        # Find workers that haven't sent heartbeat in too long
        for worker_id, last_heartbeat in self.worker_heartbeat.items():
            if current_time - last_heartbeat > WORKER_TIMEOUT:
                stale_workers.append(worker_id)

        # Remove stale workers
        for worker_id in stale_workers:
            worker_name = worker_id.decode("utf-8", errors="replace")
            model_name = self.worker_model.get(worker_id)

            if model_name:
                # Remove from queue
                if worker_id in self.worker_queue[model_name]:
                    self.worker_queue[model_name].remove(worker_id)
                    logger.warning(
                        f"Worker {worker_name} for model '{model_name}' timed out (no heartbeat)"
                    )

                # Clean up empty queues
                if not self.worker_queue[model_name]:
                    del self.worker_queue[model_name]
                    logger.info(
                        f"No workers left for model '{model_name}', removed from available models"
                    )

            # Clean up tracking dicts
            self.worker_model.pop(worker_id, None)
            self.worker_heartbeat.pop(worker_id, None)

    def stop(self):
        """Stop the broker and clean up resources."""
        logger.info("Stopping broker...")

        if self.frontend:
            self.frontend.close()
        if self.backend:
            self.backend.close()
        if self.ctx:
            self.ctx.term()

        # Clean up socket files
        self._cleanup_socket_files()

        logger.info("Broker stopped")


def run_broker(frontend_path: str | None = None, backend_path: str | None = None):
    """Run the broker process.

    Parameters
    ----------
    frontend_path : str | None
        IPC path for client connections.
    backend_path : str | None
        IPC path for worker connections.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    broker = Broker(frontend_path=frontend_path, backend_path=backend_path)
    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        broker.stop()


if __name__ == "__main__":
    run_broker()
