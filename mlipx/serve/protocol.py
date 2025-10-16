"""Protocol utilities for ZeroMQ communication with msgpack serialization."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import ase
import msgpack
import numpy as np


def get_default_broker_path() -> str:
    """Get the default broker path based on the platform.

    Returns
    -------
    str
        Default IPC path for the broker socket.

    Notes
    -----
    - Linux: `ipc:///run/user/{uid}/mlipx/broker.ipc` (if available) or `ipc:///tmp/mlipx/broker.ipc`
    - macOS: `ipc:///tmp/mlipx/broker.ipc`
    - Windows: `ipc:///{TEMP}/mlipx/broker.ipc`
    """
    if sys.platform == "win32":
        base_dir = Path(tempfile.gettempdir()) / "mlipx"
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"ipc:///{base_dir}/broker.ipc"
    elif sys.platform == "linux":
        # Try XDG_RUNTIME_DIR first
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if runtime_dir:
            base_dir = Path(runtime_dir) / "mlipx"
            base_dir.mkdir(parents=True, exist_ok=True)
            return f"ipc://{base_dir}/broker.ipc"
        # Fall back to /tmp
        base_dir = Path("/tmp/mlipx")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"ipc://{base_dir}/broker.ipc"
    else:  # macOS and other Unix-like systems
        base_dir = Path("/tmp/mlipx")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"ipc://{base_dir}/broker.ipc"


def get_default_workers_path() -> str:
    """Get the default workers backend path based on the platform.

    Returns
    -------
    str
        Default IPC path for the workers backend socket.
    """
    broker_path = get_default_broker_path()
    # Replace broker.ipc with workers.ipc
    return broker_path.replace("broker.ipc", "workers.ipc")


def check_broker_socket_exists(broker_path: str) -> bool:
    """Check if the broker socket file exists.

    Parameters
    ----------
    broker_path : str
        IPC path to broker socket (e.g., 'ipc:///tmp/mlipx/workers.ipc')

    Returns
    -------
    bool
        True if socket file exists, False otherwise.
    """
    if broker_path.startswith("ipc://"):
        socket_path = Path(broker_path[6:])
        return socket_path.exists()
    return False


def pack_request(atoms: ase.Atoms, properties: list[str] | None = None) -> bytes:
    """Pack an ASE Atoms object into a msgpack request.

    Parameters
    ----------
    atoms : ase.Atoms
        The atoms to pack.
    properties : list[str] | None
        Properties to calculate. Defaults to ['energy', 'forces'].

    Returns
    -------
    bytes
        Msgpack-encoded request data.
    """
    if properties is None:
        properties = ["energy", "forces"]

    request = {
        "numbers": atoms.numbers.astype(np.int32).tobytes(),
        "positions": atoms.positions.astype(np.float64).tobytes(),
        "cell": np.array(atoms.cell).astype(np.float64).tobytes(),
        "pbc": np.array(atoms.pbc).tobytes(),
        "properties": properties,
    }
    return msgpack.packb(request)


def unpack_request(data: bytes) -> tuple[ase.Atoms, list[str]]:
    """Unpack a msgpack request into an ASE Atoms object and properties list.

    Parameters
    ----------
    data : bytes
        Msgpack-encoded request data.

    Returns
    -------
    tuple[ase.Atoms, list[str]]
        The atoms object and list of properties to calculate.
    """
    request = msgpack.unpackb(data)

    numbers = np.frombuffer(request["numbers"], dtype=np.int32)
    positions = np.frombuffer(request["positions"], dtype=np.float64).reshape(-1, 3)
    cell = np.frombuffer(request["cell"], dtype=np.float64).reshape(3, 3)
    pbc = np.frombuffer(request["pbc"], dtype=bool)
    properties = request.get("properties", ["energy", "forces"])

    atoms = ase.Atoms(numbers=numbers, positions=positions, cell=cell, pbc=pbc)
    return atoms, properties


def pack_response(
    success: bool,
    energy: float | None = None,
    forces: np.ndarray | None = None,
    stress: np.ndarray | None = None,
    error: str | None = None,
) -> bytes:
    """Pack a calculation response into msgpack format.

    Parameters
    ----------
    success : bool
        Whether the calculation succeeded.
    energy : float | None
        Energy in eV (if requested and successful).
    forces : np.ndarray | None
        Forces in eV/Ang, shape (N, 3) (if requested and successful).
    stress : np.ndarray | None
        Stress in eV/Ang^3, shape (6,) (if requested and successful).
    error : str | None
        Error message if success is False.

    Returns
    -------
    bytes
        Msgpack-encoded response data.
    """
    response: dict[str, Any] = {"success": success}

    if success:
        if energy is not None:
            response["energy"] = float(energy)
        if forces is not None:
            response["forces"] = forces.astype(np.float64).tobytes()
        if stress is not None:
            response["stress"] = stress.astype(np.float64).tobytes()
    else:
        response["error"] = error

    return msgpack.packb(response)


def unpack_response(data: bytes) -> dict[str, Any]:
    """Unpack a msgpack response.

    Parameters
    ----------
    data : bytes
        Msgpack-encoded response data.

    Returns
    -------
    dict[str, Any]
        Response dictionary with keys:
        - success: bool
        - energy: float (if requested and successful)
        - forces: np.ndarray (if requested and successful)
        - stress: np.ndarray (if requested and successful)
        - error: str (if not successful)
    """
    response = msgpack.unpackb(data)

    # Decode binary arrays back to numpy
    if "forces" in response:
        forces_bytes = response["forces"]
        n_atoms = len(forces_bytes) // (3 * 8)  # 3 coordinates * 8 bytes per float64
        response["forces"] = np.frombuffer(forces_bytes, dtype=np.float64).reshape(
            n_atoms, 3
        )

    if "stress" in response:
        response["stress"] = np.frombuffer(response["stress"], dtype=np.float64)

    return response


# Message type constants
READY = b"READY"
HEARTBEAT = b"HEARTBEAT"
LIST_MODELS = b"LIST_MODELS"
STATUS_DETAIL = b"STATUS_DETAIL"
