"""Integration tests for the serve module."""

import subprocess
import sys
import time

import numpy as np
import pytest


def _serve_available() -> bool:
    """Check if serve dependencies are installed."""
    try:
        import msgpack  # noqa: F401
        import zmq  # noqa: F401

        return True
    except ImportError:
        return False


# Skip all tests in this module if serve dependencies are not installed
pytestmark = pytest.mark.skipif(
    not _serve_available(),
    reason="mlipx[serve] not installed",
)


@pytest.fixture
def broker_process(tmp_path):
    """Start a broker process for testing."""
    socket_path = tmp_path / "test-broker.ipc"
    broker_path = f"ipc://{socket_path}"
    workers_path = f"ipc://{tmp_path / 'test-workers.ipc'}"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"""
import sys
sys.path.insert(0, '.')
from mlipx.serve import Broker
broker = Broker(frontend_path='{broker_path}', backend_path='{workers_path}')
broker.start()
""",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(tmp_path.parent.parent.parent),  # mlipx root
    )

    # Wait for broker to start and create socket
    max_wait = 5.0
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if socket_path.exists():
            break
        time.sleep(0.1)

    yield broker_path, proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


class TestProtocolSerializaton:
    """Test protocol pack/unpack functions."""

    def test_pack_unpack_request_roundtrip(self):
        """Test that pack/unpack request functions are inverses."""
        from ase import Atoms

        from mlipx.serve.protocol import pack_request, unpack_request

        # Create test atoms
        atoms = Atoms(
            "H2O", positions=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        )
        atoms.set_cell([10.0, 10.0, 10.0])
        atoms.set_pbc([True, True, True])
        properties = ["energy", "forces", "stress"]

        # Pack and unpack
        packed = pack_request(atoms, properties)
        unpacked_atoms, unpacked_props = unpack_request(packed)

        # Verify
        assert len(unpacked_atoms) == len(atoms)
        assert list(unpacked_atoms.numbers) == list(atoms.numbers)
        np.testing.assert_array_almost_equal(unpacked_atoms.positions, atoms.positions)
        np.testing.assert_array_almost_equal(
            np.array(unpacked_atoms.cell), np.array(atoms.cell)
        )
        assert list(unpacked_atoms.pbc) == list(atoms.pbc)
        assert unpacked_props == properties

    def test_pack_unpack_response_success(self):
        """Test packing and unpacking successful response."""
        from mlipx.serve.protocol import pack_response, unpack_response

        energy = -123.456
        forces = np.array([[1.0, 2.0, 3.0], [-1.0, -2.0, -3.0]])
        stress = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        packed = pack_response(
            success=True, energy=energy, forces=forces, stress=stress
        )
        response = unpack_response(packed)

        assert response["success"] is True
        assert response["energy"] == pytest.approx(energy)
        np.testing.assert_array_almost_equal(response["forces"], forces)
        np.testing.assert_array_almost_equal(response["stress"], stress)

    def test_pack_unpack_response_error(self):
        """Test packing and unpacking error response."""
        from mlipx.serve.protocol import pack_response, unpack_response

        error_msg = "Something went wrong"
        packed = pack_response(success=False, error=error_msg)
        response = unpack_response(packed)

        assert response["success"] is False
        assert response["error"] == error_msg


class TestBrokerStatus:
    """Test broker status functions."""

    def test_get_broker_status_not_running(self, tmp_path):
        """Test status when broker is not running."""
        from mlipx.serve import get_broker_status

        fake_path = f"ipc://{tmp_path}/nonexistent.ipc"
        status = get_broker_status(broker_path=fake_path)

        assert status["broker_running"] is False
        assert status["broker_path"] == fake_path
        assert status["models"] == []
        assert status["error"] is not None

    def test_get_broker_status_running(self, broker_process):
        """Test status when broker is running."""
        from mlipx.serve import get_broker_status

        broker_path, _ = broker_process
        status = get_broker_status(broker_path=broker_path)

        assert status["broker_running"] is True
        assert status["broker_path"] == broker_path
        assert status["models"] == []  # No workers registered
        assert status["error"] is None

    def test_get_broker_detailed_status(self, broker_process):
        """Test detailed status when broker is running."""
        from mlipx.serve import get_broker_detailed_status

        broker_path, _ = broker_process
        status = get_broker_detailed_status(broker_path=broker_path)

        assert status["broker_running"] is True
        assert status["broker_path"] == broker_path
        assert status["models"] == {}  # No workers registered
        assert status["autostart"] is False  # Basic broker, not autostart
        assert status["error"] is None


class TestModelsClass:
    """Test the Models collection class."""

    def test_models_empty_when_no_workers(self, broker_process):
        """Test Models class returns empty when no workers registered."""
        from mlipx.serve import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path)

        assert list(models) == []
        assert len(models) == 0

    def test_models_contains_returns_false(self, broker_process):
        """Test __contains__ returns False for unavailable model."""
        from mlipx.serve import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path)

        assert "nonexistent-model" not in models

    def test_models_getitem_raises_keyerror(self, broker_process):
        """Test __getitem__ raises KeyError for unavailable model."""
        from mlipx.serve import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path)

        with pytest.raises(KeyError, match="not available"):
            _ = models["nonexistent-model"]


class TestDefaultPaths:
    """Test default path generation."""

    def test_default_broker_path_not_empty(self):
        """Test that default broker path is generated."""
        from mlipx.serve import get_default_broker_path

        path = get_default_broker_path()
        assert path.startswith("ipc://")
        assert "mlipx" in path

    def test_default_workers_path_not_empty(self):
        """Test that default workers path is generated."""
        from mlipx.serve import get_default_workers_path

        path = get_default_workers_path()
        assert path.startswith("ipc://")
        assert "workers" in path

    def test_workers_path_derived_from_broker_path(self):
        """Test workers path is derived from broker path."""
        from mlipx.serve import get_default_broker_path, get_default_workers_path

        broker = get_default_broker_path()
        workers = get_default_workers_path()

        # Workers path should be same directory as broker
        broker_dir = broker.rsplit("/", 1)[0]
        workers_dir = workers.rsplit("/", 1)[0]
        assert broker_dir == workers_dir


class TestGenericASECalculatorServeIntegration:
    """Test GenericASECalculator serve_name field."""

    def test_serve_name_field_exists(self):
        """Test that serve_name field is available."""
        from mlipx import GenericASECalculator

        calc = GenericASECalculator(
            module="ase.calculators.lj",
            class_name="LennardJones",
            serve_name="test-model",
        )

        assert calc.serve_name == "test-model"

    def test_serve_name_defaults_to_none(self):
        """Test that serve_name defaults to None."""
        from mlipx import GenericASECalculator

        calc = GenericASECalculator(
            module="ase.calculators.lj",
            class_name="LennardJones",
        )

        assert calc.serve_name is None
