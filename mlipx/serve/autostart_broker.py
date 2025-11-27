"""Broker with automatic worker starting capabilities."""

import logging
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import msgpack

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
        worker_start_timeout: int = 180,
        worker_run_timeout: int = 30,
        allowed_models: list[str] | None = None,
        concurrency: int = 1,
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
            Default is 180 seconds.
        worker_run_timeout : int
            Maximum time in seconds for a single calculation.
            Default is 30 seconds.
        allowed_models : list[str] | None
            Optional list of model names to serve. If None, all models from
            the registry are available. If specified, only these models can
            be auto-started.
        concurrency : int
            Maximum number of worker processes to auto-start per model.
            Default is 1. External workers can still connect beyond this limit.
        """
        super().__init__(frontend_path, backend_path, worker_run_timeout)

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
            model_names = ", ".join(sorted(self.models_registry.keys()))
            logger.info(f"Serving {len(self.models_registry)} models: [{model_names}]")
        else:
            self.models_registry = all_models
            model_names = ", ".join(sorted(self.models_registry.keys()))
            logger.info(
                f"Serving all {len(self.models_registry)} models from registry: "
                f"[{model_names}]"
            )

        # Track worker processes: {model_name: [Popen, ...]}
        # Supports multiple workers per model for concurrency
        self.worker_processes: dict[str, list[subprocess.Popen]] = defaultdict(list)
        self.worker_timeout = worker_timeout
        self.worker_start_timeout = worker_start_timeout
        self.worker_run_timeout = worker_run_timeout
        self.concurrency = concurrency
        self.models_file = models_file  # Store for passing to workers

        # Queue for requests waiting for a worker:
        # {model_name: [(client_id, request_data), ...]}
        # Implements FIFO ordering for requests when workers are busy
        self._request_queue: dict[str, list[tuple[bytes, bytes]]] = defaultdict(list)

        # Track in-flight requests: {worker_id: (client_id, start_time, model_name)}
        # Used to detect workers that are stuck and need to be killed
        self._in_flight_requests: dict[bytes, tuple[bytes, float, str]] = {}

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
                    "worker_run_timeout": self.worker_run_timeout,
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

        # Check if model is in registry
        if model_name not in self.models_registry:
            error_response = msgpack.packb(
                {
                    "success": False,
                    "error": f"Model '{model_name}' not found in registry",
                }
            )
            self.frontend.send_multipart([client_id, b"", error_response])
            logger.warning(f"Model '{model_name}' not in registry")
            return

        # Try to route to an available worker, or queue the request
        self._route_or_queue_request(client_id, model_name, request_data)

    def _route_or_queue_request(
        self, client_id: bytes, model_name: str, request_data: bytes
    ):
        """Route request to available worker or queue it for later.

        This implements proper FIFO ordering:
        1. If a worker is available, route immediately
        2. If no worker available but process is starting, queue the request
        3. If no worker process exists, start one and queue the request
        """
        # Check if we have an available worker
        if model_name in self.worker_queue and self.worker_queue[model_name]:
            # Worker available - route immediately
            worker_id = self.worker_queue[model_name].popleft()
            self._send_to_worker(worker_id, client_id, model_name, request_data)
            return

        # No available worker - need to queue request and possibly start worker
        queue_position = len(self._request_queue[model_name])
        self._request_queue[model_name].append((client_id, request_data))
        logger.debug(
            f"Queued request from {client_id} for {model_name} "
            f"(queue position: {queue_position})"
        )

        # Count running worker processes for this model
        running_workers = self._count_running_workers(model_name)

        if running_workers >= self.concurrency:
            # At max concurrency - request is queued, will be processed
            # when a worker sends READY
            logger.debug(
                f"Worker(s) for {model_name} busy ({running_workers} running), "
                "request queued"
            )
        else:
            # Can start more workers
            logger.info(
                f"Starting worker for {model_name} "
                f"({running_workers}/{self.concurrency} running)..."
            )
            self._start_worker(model_name)

    def _send_to_worker(
        self, worker_id: bytes, client_id: bytes, model_name: str, request_data: bytes
    ):
        """Send a request to a specific worker and track it."""
        # Track the in-flight request
        self._in_flight_requests[worker_id] = (client_id, time.time(), model_name)

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
        worker_name = worker_id.decode("utf-8", errors="replace")
        logger.debug(f"Routed request from {client_id} to {worker_name} ({model_name})")

    def _handle_backend(self):
        """Handle messages from workers, processing queued requests when ready.

        Extends parent to:
        1. Clear in-flight tracking when response received
        2. Process queued requests when worker becomes available (READY)
        """
        from .protocol import HEARTBEAT, READY

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

            # Clear in-flight tracking for this worker
            self._in_flight_requests.pop(worker_id, None)

            # Register the worker (adds to queue)
            self._register_worker(worker_id, model_name)

            # Check if there are queued requests for this model
            if self._request_queue[model_name]:
                # Pop from front of queue (FIFO)
                client_id, request_data = self._request_queue[model_name].pop(0)

                # The worker just registered, so it should be in the queue
                # Pop it back out to handle this request
                if (
                    model_name in self.worker_queue
                    and worker_id in self.worker_queue[model_name]
                ):
                    self.worker_queue[model_name].remove(worker_id)

                self._send_to_worker(worker_id, client_id, model_name, request_data)
                worker_name = worker_id.decode("utf-8", errors="replace")
                remaining = len(self._request_queue[model_name])
                logger.debug(
                    f"Dispatched queued request to {worker_name} "
                    f"(queue remaining: {remaining})"
                )

        elif message_type == HEARTBEAT:
            # HEARTBEAT message: [worker_id, b"", HEARTBEAT, model_name]
            if len(parts) < 4:
                logger.warning(f"Invalid HEARTBEAT message from worker {worker_id}")
                return

            # Update heartbeat timestamp
            self.worker_heartbeat[worker_id] = time.time()
            worker_name = worker_id.decode("utf-8", errors="replace")
            logger.debug(f"Received heartbeat from worker {worker_name}")

        else:
            # Response message: [worker_id, b"", client_id, b"", response_data]
            if len(parts) < 5:
                logger.warning(f"Invalid response from worker {worker_id}: {parts}")
                return

            client_id = parts[2]
            response_data = parts[4]

            # Forward response to client
            self.frontend.send_multipart([client_id, b"", response_data])
            worker_name = worker_id.decode("utf-8", errors="replace")
            logger.debug(f"Routed response from {worker_name} to {client_id}")

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

    def _count_running_workers(self, model_name: str) -> int:
        """Count running worker processes for a model.

        Also cleans up terminated processes from the list.
        """
        if model_name not in self.worker_processes:
            return 0

        # Filter to only running processes, cleaning up terminated ones
        running = []
        for proc in self.worker_processes[model_name]:
            if proc.poll() is None:
                running.append(proc)
        self.worker_processes[model_name] = running
        return len(running)

    def _start_worker(self, model_name: str):
        """Start a worker using mlipx serve.

        Parameters
        ----------
        model_name : str
            Name of the model to serve.
        """
        # Check if at max concurrency
        running_count = self._count_running_workers(model_name)
        if running_count >= self.concurrency:
            logger.debug(
                f"Already at max concurrency for {model_name} "
                f"({running_count}/{self.concurrency})"
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
            self.worker_processes[model_name].append(proc)
            logger.info(
                f"Worker started for {model_name} (PID: {proc.pid}, "
                f"total: {len(self.worker_processes[model_name])})"
            )
        except Exception as e:
            logger.error(f"Failed to start worker for {model_name}: {e}", exc_info=True)

    def _check_worker_health(self):  # noqa: C901
        """Check for stale workers and remove them, killing processes if needed.

        This extends the parent implementation to:
        1. Detect in-flight requests that exceeded worker_run_timeout
        2. Send error responses to affected clients
        3. Kill the worker process if we started it
        4. Clean up terminated processes
        5. Restart worker if there are queued requests
        """
        current_time = time.time()

        # First, clean up stale in-flight entries for workers that no longer exist
        # This can happen when a worker terminates gracefully (idle timeout)
        stale_entries = []
        for worker_id in list(self._in_flight_requests.keys()):
            if worker_id not in self.worker_model:
                stale_entries.append(worker_id)

        for worker_id in stale_entries:
            client_id, start_time, model_name = self._in_flight_requests.pop(worker_id)
            worker_name = worker_id.decode("utf-8", errors="replace")
            logger.warning(
                f"Cleaning up stale in-flight entry for defunct worker {worker_name}"
            )
            # The worker is gone but the client never got a response - send error
            error_response = msgpack.packb(
                {
                    "success": False,
                    "error": "Worker disconnected unexpectedly",
                }
            )
            self.frontend.send_multipart([client_id, b"", error_response])

            # Re-queue this request or start a new worker
            if self._request_queue[model_name] or True:  # Always try to recover
                logger.info(f"Will restart worker for {model_name} after cleanup")
                self._start_worker(model_name)

        # Find workers with in-flight requests that exceeded timeout
        workers_to_kill = []
        for worker_id, (client_id, start_time, model_name) in list(
            self._in_flight_requests.items()
        ):
            # Only timeout if worker is still known (not already cleaned up)
            if worker_id in self.worker_model:
                if current_time - start_time > self.worker_run_timeout:
                    workers_to_kill.append((worker_id, client_id, model_name))

        # Handle stuck workers
        for worker_id, client_id, model_name in workers_to_kill:
            worker_name = worker_id.decode("utf-8", errors="replace")
            logger.warning(
                f"Worker {worker_name} for '{model_name}' exceeded run_timeout "
                f"({self.worker_run_timeout}s)"
            )

            # Send error to client
            error_response = msgpack.packb(
                {
                    "success": False,
                    "error": (
                        f"Calculation timed out after {self.worker_run_timeout}s. "
                        f"Worker was killed."
                    ),
                }
            )
            self.frontend.send_multipart([client_id, b"", error_response])
            logger.info(f"Sent timeout error to client {client_id}")

            # Remove from in-flight tracking
            self._in_flight_requests.pop(worker_id, None)

            # Kill all worker processes for this model if we started them
            # (We don't know which specific process is stuck, so kill all)
            if model_name in self.worker_processes:
                for proc in self.worker_processes[model_name]:
                    if proc.poll() is None:  # Still running
                        logger.warning(f"Killing worker process (PID: {proc.pid})")
                        try:
                            proc.kill()  # SIGKILL - immediate termination
                            proc.wait(timeout=5)
                            logger.info(f"Killed worker for {model_name}")
                        except Exception as e:
                            logger.error(f"Error killing worker for {model_name}: {e}")
                # Clear the list
                self.worker_processes[model_name] = []

            # Clean up worker from broker tracking
            if worker_id in self.worker_model:
                del self.worker_model[worker_id]
            if worker_id in self.worker_heartbeat:
                del self.worker_heartbeat[worker_id]
            if (
                model_name in self.worker_queue
                and worker_id in self.worker_queue[model_name]
            ):
                self.worker_queue[model_name].remove(worker_id)
                if not self.worker_queue[model_name]:
                    del self.worker_queue[model_name]

            # If there are queued requests, restart a worker
            if self._request_queue[model_name]:
                logger.info(
                    f"Restarting worker for {model_name} "
                    f"({len(self._request_queue[model_name])} queued requests)"
                )
                self._start_worker(model_name)

        # Clean up terminated processes and restart if needed
        for model_name in list(self.worker_processes.keys()):
            # Clean up terminated processes
            before_count = len(self.worker_processes[model_name])
            self._count_running_workers(model_name)  # This cleans up terminated
            after_count = len(self.worker_processes[model_name])

            if after_count < before_count:
                terminated_count = before_count - after_count
                logger.info(
                    f"{terminated_count} worker process(es) for {model_name} terminated"
                )

                # If there are queued requests, try to restart workers
                if self._request_queue[model_name]:
                    logger.info(
                        f"Restarting worker for {model_name} "
                        f"({len(self._request_queue[model_name])} queued requests)"
                    )
                    self._start_worker(model_name)

    def stop(self):  # noqa: C901
        """Stop the broker and clean up worker processes."""
        logger.info("Stopping autostart broker...")

        # Send error responses to any queued requests
        for model_name, requests in self._request_queue.items():
            for client_id, _ in requests:
                error_response = msgpack.packb(
                    {
                        "success": False,
                        "error": "Broker is shutting down",
                    }
                )
                try:
                    self.frontend.send_multipart([client_id, b"", error_response])
                except Exception:
                    pass  # Socket might be closed
        self._request_queue.clear()

        # Send error responses to in-flight requests
        for worker_id, (client_id, _, model_name) in self._in_flight_requests.items():
            error_response = msgpack.packb(
                {
                    "success": False,
                    "error": "Broker is shutting down",
                }
            )
            try:
                self.frontend.send_multipart([client_id, b"", error_response])
            except Exception:
                pass  # Socket might be closed
        self._in_flight_requests.clear()

        # Terminate all worker processes that we started
        for model_name, procs in list(self.worker_processes.items()):
            for proc in procs:
                if proc.poll() is None:  # Process still running
                    logger.info(
                        f"Terminating worker for {model_name} (PID: {proc.pid})"
                    )
                    try:
                        proc.terminate()  # Send SIGTERM
                        try:
                            proc.wait(
                                timeout=5
                            )  # Wait up to 5 seconds for graceful shutdown
                            logger.info(
                                f"Worker for {model_name} terminated gracefully"
                            )
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
    worker_start_timeout: int = 180,
    worker_run_timeout: int = 30,
    allowed_models: list[str] | None = None,
    concurrency: int = 1,
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
    worker_run_timeout : int
        Maximum time in seconds for a single calculation.
    allowed_models : list[str] | None
        Optional list of model names to serve. If None, all models are available.
    concurrency : int
        Maximum number of worker processes to auto-start per model.
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
        worker_run_timeout=worker_run_timeout,
        allowed_models=allowed_models,
        concurrency=concurrency,
    )
    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        broker.stop()
