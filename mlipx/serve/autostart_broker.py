"""Broker with automatic worker starting capabilities."""

import logging
import shutil
import subprocess
import time
from pathlib import Path

import msgpack
import zmq

from .broker import Broker
from .protocol import LIST_MODELS, SHUTDOWN, STATUS_DETAIL
from .worker import load_models_from_file

logger = logging.getLogger(__name__)


class AutoStartBroker(Broker):
    """Broker that automatically starts workers on demand.

    Workers handle their own shutdown after timeout - broker only spawns them.

    Design Philosophy
    -----------------
    - Broker starts workers when first request arrives for a model
    - Workers receive timeout parameter at startup
    - Workers monitor their own idle time and self-terminate after timeout
    - Broker only tracks processes to avoid duplicate starts
    - No centralized idle monitoring or worker lifecycle management
    """

    def __init__(
        self,
        frontend_path: str | None = None,
        backend_path: str | None = None,
        models_file: Path | None = None,
        worker_timeout: int = 300,
        worker_start_timeout: int = 30,
        allowed_models: list[str] | None = None,
    ):
        """Initialize the autostart broker.

        Parameters
        ----------
        frontend_path : str | None
            IPC path for client connections.
        backend_path : str | None
            IPC path for worker connections.
        models_file : Path | None
            Path to models.py file containing ALL_MODELS dict.
        worker_timeout : int
            Idle timeout in seconds for auto-started workers.
            Default is 300 seconds (5 minutes).
        worker_start_timeout : int
            Maximum time in seconds to wait for a worker to start and register.
            Default is 30 seconds.
        allowed_models : list[str] | None
            Optional list of model names to serve. If None, all models from
            the registry are available. If specified, only these models can
            be auto-started.
        """
        super().__init__(frontend_path, backend_path)

        # Load model registry
        if models_file is None:
            from mlipx import recipes

            models_file = Path(recipes.__file__).parent / "models.py.jinja2"

        logger.info(f"Loading models from {models_file}")
        all_models = load_models_from_file(models_file)

        # Filter models if allowed_models specified
        if allowed_models:
            # Validate that all requested models exist
            missing = set(allowed_models) - set(all_models.keys())
            if missing:
                available = ", ".join(sorted(all_models.keys()))
                raise ValueError(
                    f"Models not found in registry: {', '.join(sorted(missing))}. "
                    f"Available models: {available}"
                )
            self.models_registry = {k: all_models[k] for k in allowed_models}
            logger.info(f"Serving {len(self.models_registry)} models: {allowed_models}")
        else:
            self.models_registry = all_models
            logger.info(f"Serving all {len(self.models_registry)} models from registry")

        # Track worker processes to avoid duplicate starts
        self.worker_processes: dict[str, subprocess.Popen] = {}
        self.worker_timeout = worker_timeout
        self.worker_start_timeout = worker_start_timeout
        self.models_file = models_file  # Store for passing to workers

        # Queue for requests that arrive during worker startup
        self._pending_requests: list[list[bytes]] = []

    def _handle_frontend(self):  # noqa: C901
        """Handle client requests, auto-starting workers if needed."""
        parts = self.frontend.recv_multipart()

        if len(parts) < 3:
            logger.warning(f"Invalid message from client: {parts}")
            return

        client_id = parts[0]
        message_type = parts[2]

        # Handle LIST_MODELS and STATUS_DETAIL requests using parent logic
        if message_type == LIST_MODELS:
            # Return list of available models from registry (not just running workers)
            # This allows clients to see what models can be auto-started
            models = list(self.models_registry.keys())
            response = msgpack.packb({"models": models})
            self.frontend.send_multipart([client_id, b"", response])
            logger.debug(f"Sent model list to client {client_id}: {models}")
            return

        elif message_type == STATUS_DETAIL:
            # Return detailed status with worker counts per model
            model_details = {}
            for model_name, workers in self.worker_queue.items():
                model_details[model_name] = {
                    "worker_count": len(workers),
                    "workers": [
                        w.decode("utf-8", errors="replace") for w in list(workers)
                    ],
                }
            response = msgpack.packb(
                {
                    "models": model_details,
                    "autostart": True,
                    "autostart_models": list(self.models_registry.keys()),
                    "worker_start_timeout": self.worker_start_timeout,
                }
            )
            self.frontend.send_multipart([client_id, b"", response])
            logger.debug(f"Sent detailed status to client {client_id}")
            return

        elif message_type == SHUTDOWN:
            # Shutdown the broker gracefully
            logger.info(f"Received shutdown request from client {client_id}")
            response = msgpack.packb({"success": True, "message": "Shutting down"})
            self.frontend.send_multipart([client_id, b"", response])
            self.running = False
            return

        # Regular calculation request
        if len(parts) < 4:
            logger.warning(f"Invalid calculation request from client: {parts}")
            return

        model_name = message_type.decode("utf-8")
        request_data = parts[3]

        # Check if workers available
        if model_name not in self.worker_queue or not self.worker_queue[model_name]:
            # Try to autostart
            if model_name in self.models_registry:
                logger.info(f"No workers for {model_name}, auto-starting...")
                self._start_worker(model_name)

                # Wait for worker to register (with timeout), processing other messages
                start_time = time.time()
                poller = zmq.Poller()
                poller.register(self.backend, zmq.POLLIN)
                poller.register(self.frontend, zmq.POLLIN)

                while time.time() - start_time < self.worker_start_timeout:
                    # Poll both sockets with 100ms timeout
                    socks = dict(poller.poll(timeout=100))

                    if self.backend in socks:
                        self._handle_backend()

                    # Handle frontend messages during startup (queue or respond)
                    if self.frontend in socks:
                        other_parts = self.frontend.recv_multipart()
                        other_client_id = other_parts[0] if other_parts else None
                        other_msg_type = (
                            other_parts[2] if len(other_parts) > 2 else None
                        )

                        if other_msg_type == LIST_MODELS:
                            # Respond to LIST_MODELS immediately
                            models = list(self.models_registry.keys())
                            response = msgpack.packb({"models": models})
                            self.frontend.send_multipart(
                                [other_client_id, b"", response]
                            )
                        elif other_msg_type == STATUS_DETAIL:
                            # Respond to STATUS_DETAIL immediately
                            model_details = {}
                            for mn, workers in self.worker_queue.items():
                                model_details[mn] = {
                                    "worker_count": len(workers),
                                    "workers": [
                                        w.decode("utf-8", errors="replace")
                                        for w in list(workers)
                                    ],
                                }
                            response = msgpack.packb(
                                {
                                    "models": model_details,
                                    "autostart": True,
                                    "autostart_models": list(
                                        self.models_registry.keys()
                                    ),
                                    "worker_start_timeout": self.worker_start_timeout,
                                }
                            )
                            self.frontend.send_multipart(
                                [other_client_id, b"", response]
                            )
                        else:
                            # Queue calculation requests for later processing
                            self._pending_requests.append(other_parts)
                            logger.debug(
                                f"Queued request from {other_client_id} "
                                "during worker startup"
                            )

                    # Check if worker registered
                    if (
                        model_name in self.worker_queue
                        and self.worker_queue[model_name]
                    ):
                        logger.info(f"Worker for {model_name} registered successfully")
                        break
                else:
                    # Worker failed to start
                    error_msg = (
                        f"Failed to auto-start worker for '{model_name}' "
                        f"within {self.worker_start_timeout}s. "
                        f"Check terminal output for details."
                    )
                    error_response = msgpack.packb(
                        {"success": False, "error": error_msg}
                    )
                    self.frontend.send_multipart([client_id, b"", error_response])
                    logger.error(
                        f"Worker for {model_name} failed to register "
                        f"within {self.worker_start_timeout}s"
                    )
                    # Process pending requests with error
                    self._process_pending_requests()
                    return

                # Process any queued requests now that worker is ready
                self._process_pending_requests()
            else:
                # Model not in registry
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

        # Route request to worker
        # Format: [worker_id, b"", client_id, b"", model_name, request_data]
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
        logger.debug(f"Routed request from {client_id} to {worker_id} ({model_name})")

    def _process_pending_requests(self):
        """Process any requests that were queued during worker startup."""
        pending = self._pending_requests
        self._pending_requests = []

        for parts in pending:
            if len(parts) >= 4:
                client_id = parts[0]
                msg_type = parts[2]
                model_name = msg_type.decode("utf-8") if msg_type else None
                request_data = parts[3]

                if (
                    model_name
                    and model_name in self.worker_queue
                    and self.worker_queue[model_name]
                ):
                    # Route to available worker
                    worker_id = self.worker_queue[model_name].popleft()
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
                        f"Processed queued request from {client_id} to {worker_id}"
                    )
                else:
                    # No workers available for this model
                    error_response = msgpack.packb(
                        {
                            "success": False,
                            "error": f"No workers available for model '{model_name}'",
                        }
                    )
                    self.frontend.send_multipart([client_id, b"", error_response])
                    logger.warning(
                        f"No workers for queued request from {client_id} ({model_name})"
                    )

    def _build_worker_command(self, model_name: str, model) -> list[str]:
        """Build the command to start a worker process.

        Uses smart dependency resolution via build_serve_command:
        - If extras exist in local pyproject.toml: uv run --extra
        - Otherwise: uvx --from mlipx[extras,serve]
        """
        from .command import build_serve_command
        from .protocol import get_default_workers_path

        # Determine broker path (only pass if non-default)
        broker_path = None
        if self.backend_path and self.backend_path != get_default_workers_path():
            broker_path = self.backend_path

        model_extras = model.extra if hasattr(model, "extra") else None
        models_file = str(self.models_file) if self.models_file else None

        cmd, method = build_serve_command(
            model_name=model_name,
            model_extras=model_extras,
            timeout=self.worker_timeout,
            broker=broker_path,
            models_file=models_file,
        )

        logger.info(f"Dependency resolution: {method}")
        return cmd

    def _start_worker(self, model_name: str):
        """Start a worker using mlipx serve.

        Parameters
        ----------
        model_name : str
            Name of the model to serve.
        """
        # Check if already running
        if model_name in self.worker_processes:
            proc = self.worker_processes[model_name]
            if proc.poll() is None:
                logger.debug(
                    f"Worker for {model_name} already running (PID: {proc.pid})"
                )
                return

        if not shutil.which("uv"):
            logger.error(f"Cannot auto-start {model_name}: 'uv' not found in PATH")
            return

        model = self.models_registry[model_name]
        cmd = self._build_worker_command(model_name, model)
        logger.info(f"Starting worker: {' '.join(cmd)}")

        try:
            # Inherit stdout/stderr for terminal logging
            proc = subprocess.Popen(
                cmd,
                start_new_session=True,
            )
            self.worker_processes[model_name] = proc
            logger.info(f"Worker started for {model_name} (PID: {proc.pid})")
        except Exception as e:
            logger.error(f"Failed to start worker for {model_name}: {e}", exc_info=True)

    def _check_worker_health(self):
        """Check for stale workers and remove them, cleaning up processes too."""
        # Call parent implementation first
        super()._check_worker_health()

        # Also check if any worker processes have died and clean them up
        for model_name, proc in list(self.worker_processes.items()):
            if proc.poll() is not None:  # Process has terminated
                logger.info(
                    f"Worker process for {model_name} has terminated "
                    f"(exit code: {proc.returncode})"
                )
                del self.worker_processes[model_name]

    def stop(self):
        """Stop the broker and clean up worker processes."""
        logger.info("Stopping autostart broker...")

        # Terminate all worker processes that we started
        for model_name, proc in list(self.worker_processes.items()):
            if proc.poll() is None:  # Process still running
                logger.info(f"Terminating worker for {model_name} (PID: {proc.pid})")
                try:
                    proc.terminate()  # Send SIGTERM
                    try:
                        proc.wait(
                            timeout=5
                        )  # Wait up to 5 seconds for graceful shutdown
                        logger.info(f"Worker for {model_name} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            f"Worker for {model_name} did not terminate, killing..."
                        )
                        proc.kill()  # Force kill with SIGKILL
                        proc.wait()
                        logger.info(f"Worker for {model_name} killed")
                except Exception as e:
                    logger.error(f"Error terminating worker for {model_name}: {e}")

        self.worker_processes.clear()
        super().stop()


def run_autostart_broker(
    frontend_path: str | None = None,
    backend_path: str | None = None,
    models_file: Path | None = None,
    worker_timeout: int = 300,
    worker_start_timeout: int = 30,
    allowed_models: list[str] | None = None,
):
    """Run the autostart broker process.

    Parameters
    ----------
    frontend_path : str | None
        IPC path for client connections.
    backend_path : str | None
        IPC path for worker connections.
    models_file : Path | None
        Path to models.py file containing ALL_MODELS dict.
    worker_timeout : int
        Idle timeout in seconds for auto-started workers.
    worker_start_timeout : int
        Maximum time in seconds to wait for a worker to start and register.
    allowed_models : list[str] | None
        Optional list of model names to serve. If None, all models are available.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    broker = AutoStartBroker(
        frontend_path=frontend_path,
        backend_path=backend_path,
        models_file=models_file,
        worker_timeout=worker_timeout,
        worker_start_timeout=worker_start_timeout,
        allowed_models=allowed_models,
    )
    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        broker.stop()
