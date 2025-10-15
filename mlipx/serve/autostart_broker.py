"""Broker with automatic worker starting capabilities."""

import logging
import shutil
import subprocess
import time
from pathlib import Path

import msgpack

from .broker import Broker
from .protocol import LIST_MODELS, STATUS_DETAIL
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
        """
        super().__init__(frontend_path, backend_path)

        # Load model registry
        if models_file is None:
            from mlipx import recipes

            models_file = Path(recipes.__file__).parent / "models.py.jinja2"

        logger.info(f"Loading models from {models_file}")
        self.models_registry = load_models_from_file(models_file)
        logger.info(f"Loaded {len(self.models_registry)} models from registry")

        # Track worker processes to avoid duplicate starts
        self.worker_processes: dict[str, subprocess.Popen] = {}
        self.worker_timeout = worker_timeout

    def _handle_frontend(self):
        """Handle client requests, auto-starting workers if needed."""
        parts = self.frontend.recv_multipart()

        if len(parts) < 3:
            return

        client_id = parts[0]
        message_type = parts[2]

        # For calculation requests, check if worker needed
        if message_type not in [LIST_MODELS, STATUS_DETAIL]:
            model_name = message_type.decode("utf-8")

            # Check if workers available
            if model_name not in self.worker_queue or not self.worker_queue[model_name]:
                # Try to autostart
                if model_name in self.models_registry:
                    logger.info(f"No workers for {model_name}, auto-starting...")
                    self._start_worker(model_name)

                    # Wait for worker to register (with timeout)
                    for _ in range(50):  # 5 seconds max
                        time.sleep(0.1)
                        if (
                            model_name in self.worker_queue
                            and self.worker_queue[model_name]
                        ):
                            break
                    else:
                        # Worker failed to start
                        error_response = msgpack.packb(
                            {
                                "success": False,
                                "error": f"Failed to auto-start worker for '{model_name}'",
                            }
                        )
                        self.frontend.send_multipart([client_id, b"", error_response])
                        return

        # Continue with normal request handling
        super()._handle_frontend()

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
                logger.debug(f"Worker for {model_name} already running (PID: {proc.pid})")
                return  # Already running

        model = self.models_registry[model_name]

        # Check if uv is available
        uv_path = shutil.which("uv")
        if not uv_path:
            logger.error(
                f"Cannot auto-start worker for {model_name}: 'uv' not found in PATH"
            )
            return

        # Build command: uv run --extra <deps> mlipx serve <model> --timeout <timeout> --no-uv
        cmd = ["uv", "run"]

        if hasattr(model, "extra") and model.extra:
            for dep in model.extra:
                cmd.extend(["--extra", dep])

        cmd.extend(
            [
                "mlipx",
                "serve",
                model_name,
                "--timeout",
                str(self.worker_timeout),
                "--no-uv",  # Already wrapped
            ]
        )

        # Add backend path if not default
        if self.backend_path:
            from .protocol import get_default_workers_path

            if self.backend_path != get_default_workers_path():
                cmd.extend(["--broker", self.backend_path])

        logger.info(f"Starting worker: {' '.join(cmd)}")

        try:
            # Start process (redirect output to logs)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Detach from parent
            )

            self.worker_processes[model_name] = proc
            logger.info(f"Worker process started for {model_name} (PID: {proc.pid})")
        except Exception as e:
            logger.error(f"Failed to start worker for {model_name}: {e}", exc_info=True)

    def stop(self):
        """Stop the broker and clean up worker processes."""
        logger.info("Stopping autostart broker...")

        # Note: We don't kill worker processes here because they manage
        # their own lifecycle via timeout. They will shut down gracefully
        # when they detect the broker is gone or timeout.

        super().stop()


def run_autostart_broker(
    frontend_path: str | None = None,
    backend_path: str | None = None,
    models_file: Path | None = None,
    worker_timeout: int = 300,
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
    )
    try:
        broker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        broker.stop()
