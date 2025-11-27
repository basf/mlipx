"""Integration tests for the serve module."""

import subprocess
import sys
import time
from email.message import Message
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestGetMlipxPackageSpec:
    """Test the _get_mlipx_package_spec helper function."""

    def test_release_version_uses_pypi(self):
        """Test that release versions use PyPI with pinned version."""
        from mlipx.serve.command import _get_mlipx_package_spec

        with patch("mlipx.__version__", "0.1.6"):
            # Mock metadata to not have Source Commit URL
            mock_metadata = Message()
            with patch("importlib.metadata.metadata", return_value=mock_metadata):
                result = _get_mlipx_package_spec(["mace", "serve"])

        assert result == "mlipx[mace,serve]==0.1.6"

    def test_dev_version_uses_git_url_from_metadata(self):
        """Test that dev versions use git URL from Source Commit metadata."""
        from mlipx.serve.command import _get_mlipx_package_spec

        with patch("mlipx.__version__", "0.1.6.dev17+gabc123def"):
            # Mock metadata with Source Commit URL
            mock_metadata = MagicMock()
            mock_metadata.items.return_value = [
                ("Project-URL", "Homepage, https://github.com/basf/mlipx"),
                (
                    "Project-URL",
                    "Source Commit, https://github.com/basf/mlipx/tree/abc123def",
                ),
            ]
            with patch("importlib.metadata.metadata", return_value=mock_metadata):
                result = _get_mlipx_package_spec(["mace", "serve"])

        assert result == (
            "mlipx[mace,serve] @ git+https://github.com/basf/mlipx@abc123def"
        )

    def test_dev_version_without_source_commit_uses_pypi(self):
        """Test that dev versions without Source Commit fall back to PyPI."""
        from mlipx.serve.command import _get_mlipx_package_spec

        with patch("mlipx.__version__", "0.1.6.dev0"):
            # Mock metadata without Source Commit URL
            mock_metadata = MagicMock()
            mock_metadata.items.return_value = [
                ("Project-URL", "Homepage, https://github.com/basf/mlipx"),
            ]
            with patch("importlib.metadata.metadata", return_value=mock_metadata):
                result = _get_mlipx_package_spec(["mace", "serve"])

        assert result == "mlipx[mace,serve]"

    def test_no_version_uses_latest_pypi(self):
        """Test that no version uses latest from PyPI."""
        from mlipx.serve.command import _get_mlipx_package_spec

        with patch("mlipx.__version__", None):
            result = _get_mlipx_package_spec(["mace", "serve"])

        assert result == "mlipx[mace,serve]"

    def test_single_extra(self):
        """Test with a single extra."""
        from mlipx.serve.command import _get_mlipx_package_spec

        with patch("mlipx.__version__", "1.0.0"):
            mock_metadata = Message()
            with patch("importlib.metadata.metadata", return_value=mock_metadata):
                result = _get_mlipx_package_spec(["serve"])

        assert result == "mlipx[serve]==1.0.0"


class TestGetLocalPyprojectExtras:
    """Test the _get_local_pyproject_extras helper function."""

    def test_returns_extras_from_pyproject(self, tmp_path, monkeypatch):
        """Test that it returns extras from local pyproject.toml."""
        from mlipx.serve.command import _get_local_pyproject_extras

        # Create a pyproject.toml with extras
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test"

[project.optional-dependencies]
mace = ["mace-torch"]
serve = ["pyzmq"]
dev = ["pytest"]
""")

        monkeypatch.chdir(tmp_path)
        result = _get_local_pyproject_extras()

        assert result == {"mace", "serve", "dev"}

    def test_returns_empty_when_no_pyproject(self, tmp_path, monkeypatch):
        """Test that it returns empty set when no pyproject.toml exists."""
        from mlipx.serve.command import _get_local_pyproject_extras

        monkeypatch.chdir(tmp_path)
        result = _get_local_pyproject_extras()

        assert result == set()

    def test_returns_empty_when_no_extras(self, tmp_path, monkeypatch):
        """Test that it returns empty set when pyproject has no extras."""
        from mlipx.serve.command import _get_local_pyproject_extras

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test"
""")

        monkeypatch.chdir(tmp_path)
        result = _get_local_pyproject_extras()

        assert result == set()


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
        from mlipx import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path, local=False)

        assert list(models) == []
        assert len(models) == 0

    def test_models_contains_returns_false(self, broker_process):
        """Test __contains__ returns False for unavailable model."""
        from mlipx import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path, local=False)

        assert "nonexistent-model" not in models

    def test_models_getitem_raises_keyerror(self, broker_process):
        """Test __getitem__ raises KeyError for unavailable model."""
        from mlipx import Models

        broker_path, _ = broker_process
        models = Models(broker=broker_path, local=False)

        with pytest.raises(KeyError, match="not found"):
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


class TestDiscoverModelsFile:
    """Test the discover_models_file function."""

    def test_explicit_path_exists(self, tmp_path):
        """Test discovery with explicit path that exists."""
        from mlipx.serve.discovery import discover_models_file

        # Create a valid models file
        models_file = tmp_path / "custom_models.py"
        models_file.write_text("ALL_MODELS = {}")

        path, source = discover_models_file(explicit_path=models_file)

        assert path == models_file
        assert source == "explicit --models flag"

    def test_explicit_path_not_exists(self, tmp_path):
        """Test discovery with explicit path that doesn't exist."""
        from mlipx.serve.discovery import discover_models_file

        nonexistent = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError, match="Models file not found"):
            discover_models_file(explicit_path=nonexistent)

    def test_env_var_override(self, tmp_path, monkeypatch):
        """Test discovery via MLIPX_MODELS environment variable."""
        from mlipx.serve.discovery import discover_models_file

        # Create a models file
        models_file = tmp_path / "env_models.py"
        models_file.write_text("ALL_MODELS = {'test': None}")

        monkeypatch.setenv("MLIPX_MODELS", str(models_file))

        path, source = discover_models_file()

        assert path == models_file
        assert source == "MLIPX_MODELS environment variable"

    def test_env_var_not_exists(self, tmp_path, monkeypatch):
        """Test discovery with MLIPX_MODELS pointing to nonexistent file."""
        from mlipx.serve.discovery import discover_models_file

        monkeypatch.setenv("MLIPX_MODELS", str(tmp_path / "nonexistent.py"))

        with pytest.raises(FileNotFoundError, match="MLIPX_MODELS"):
            discover_models_file()

    def test_upward_search_finds_models_py(self, tmp_path):
        """Test discovery searches upward for models.py."""
        from mlipx.serve.discovery import discover_models_file

        # Create directory structure: tmp_path/models.py, tmp_path/sub/sub2/
        models_file = tmp_path / "models.py"
        models_file.write_text("ALL_MODELS = {'found': True}")

        subdir = tmp_path / "sub" / "sub2"
        subdir.mkdir(parents=True)

        # Search from subdir should find models.py in parent
        path, source = discover_models_file(start_dir=subdir)

        assert path == models_file
        assert "discovered" in source

    def test_upward_search_ignores_non_mlipx_models(self, tmp_path):
        """Test that models.py without ALL_MODELS is ignored."""
        from mlipx.serve.discovery import discover_models_file

        # Create a models.py without ALL_MODELS (e.g., Django models)
        models_file = tmp_path / "models.py"
        models_file.write_text("class User:\n    pass")

        # Should fall back to built-in default
        path, source = discover_models_file(start_dir=tmp_path)

        assert "models.py.jinja2" in str(path)
        assert source == "built-in package default"

    def test_fallback_to_builtin(self, tmp_path):
        """Test fallback to built-in default when nothing found."""
        from mlipx.serve.discovery import discover_models_file

        # Empty directory, no models.py
        path, source = discover_models_file(start_dir=tmp_path)

        assert "models.py.jinja2" in str(path)
        assert source == "built-in package default"

    def test_explicit_path_takes_precedence(self, tmp_path, monkeypatch):
        """Test that explicit path takes precedence over env var."""
        from mlipx.serve.discovery import discover_models_file

        # Create two models files
        explicit_file = tmp_path / "explicit.py"
        explicit_file.write_text("ALL_MODELS = {'explicit': True}")

        env_file = tmp_path / "env.py"
        env_file.write_text("ALL_MODELS = {'env': True}")

        monkeypatch.setenv("MLIPX_MODELS", str(env_file))

        # Explicit should win
        path, source = discover_models_file(explicit_path=explicit_file)

        assert path == explicit_file
        assert source == "explicit --models flag"


class TestAutoStartBrokerModelFiltering:
    """Test AutoStartBroker model filtering functionality."""

    def test_allowed_models_filters_registry(self, tmp_path):
        """Test that allowed_models filters the registry."""
        from mlipx.serve.autostart_broker import AutoStartBroker

        # Create a models file with multiple models
        models_file = tmp_path / "models.py"
        models_file.write_text("""
from mlipx import GenericASECalculator
ALL_MODELS = {
    'model-a': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
    'model-b': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
    'model-c': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
}
""")

        # Create broker with only model-a and model-b allowed
        broker = AutoStartBroker(
            frontend_path=f"ipc://{tmp_path}/broker.ipc",
            models_file=models_file,
            allowed_models=["model-a", "model-b"],
        )

        assert "model-a" in broker.models_registry
        assert "model-b" in broker.models_registry
        assert "model-c" not in broker.models_registry
        assert len(broker.models_registry) == 2

        # Clean up
        broker._release_lock()

    def test_allowed_models_validates_existence(self, tmp_path):
        """Test that allowed_models validates model names exist."""
        from mlipx.serve.autostart_broker import AutoStartBroker

        models_file = tmp_path / "models.py"
        models_file.write_text("""
from mlipx import GenericASECalculator
ALL_MODELS = {
    'model-a': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
}
""")

        with pytest.raises(ValueError, match="Models not found in registry"):
            AutoStartBroker(
                frontend_path=f"ipc://{tmp_path}/broker.ipc",
                models_file=models_file,
                allowed_models=["model-a", "nonexistent"],
            )

    def test_no_allowed_models_serves_all(self, tmp_path):
        """Test that None allowed_models serves all models."""
        from mlipx.serve.autostart_broker import AutoStartBroker

        models_file = tmp_path / "models.py"
        models_file.write_text("""
from mlipx import GenericASECalculator
ALL_MODELS = {
    'model-a': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
    'model-b': GenericASECalculator(
        module='ase.calculators.lj', class_name='LennardJones'
    ),
}
""")

        broker = AutoStartBroker(
            frontend_path=f"ipc://{tmp_path}/broker.ipc",
            models_file=models_file,
            allowed_models=None,
        )

        assert len(broker.models_registry) == 2
        assert "model-a" in broker.models_registry
        assert "model-b" in broker.models_registry

        # Clean up
        broker._release_lock()


class TestModelsLocalWithLJCalculator:
    """Integration tests for Models class with a dummy LJ calculator."""

    @pytest.fixture
    def lj_models_file(self, tmp_path):
        """Create a models.py file with a Lennard-Jones calculator."""
        models_file = tmp_path / "models.py"
        models_file.write_text("""
from mlipx import GenericASECalculator

ALL_MODELS = {
    'lj-test': GenericASECalculator(
        module='ase.calculators.lj',
        class_name='LennardJones',
    ),
}
""")
        return models_file

    def test_models_local_loads_lj_model(self, lj_models_file):
        """Test that Models can load a local LJ model."""
        from mlipx import Models

        models = Models(path=lj_models_file, local=True)

        assert "lj-test" in models
        assert len(models) == 1
        assert list(models) == ["lj-test"]

    def test_models_local_get_calculator(self, lj_models_file):
        """Test that get_calculator returns a working calculator."""
        from ase import Atoms

        from mlipx import Models

        models = Models(path=lj_models_file, local=True)
        calc = models["lj-test"].get_calculator()

        # Create simple atoms and compute energy
        atoms = Atoms("Ar2", positions=[[0, 0, 0], [3.0, 0, 0]])
        atoms.calc = calc

        energy = atoms.get_potential_energy()
        forces = atoms.get_forces()

        assert isinstance(energy, float)
        assert forces.shape == (2, 3)

    def test_models_local_geometry_optimization(self, lj_models_file):
        """Test running a geometry optimization with local LJ model."""
        from ase import Atoms
        from ase.optimize import BFGS

        from mlipx import Models

        models = Models(path=lj_models_file, local=True)
        calc = models["lj-test"].get_calculator()

        # Create two Ar atoms at non-equilibrium distance (too far apart)
        atoms = Atoms("Ar2", positions=[[0, 0, 0], [4.0, 0, 0]])
        atoms.calc = calc

        # Run optimization
        optimizer = BFGS(atoms, logfile=None)
        converged = optimizer.run(fmax=0.01, steps=50)

        # Should converge
        assert converged
        # Final forces should be small
        max_force = max(abs(atoms.get_forces().flatten()))
        assert max_force < 0.02

    def test_models_local_repr(self, lj_models_file):
        """Test Models repr includes model names."""
        from mlipx import Models

        models = Models(path=lj_models_file, local=True)

        repr_str = repr(models)
        assert "lj-test" in repr_str
        assert "local" in repr_str

    def test_models_local_keyerror_for_missing_model(self, lj_models_file):
        """Test KeyError is raised for non-existent model."""
        from mlipx import Models

        models = Models(path=lj_models_file, local=True)

        with pytest.raises(KeyError, match="nonexistent"):
            _ = models["nonexistent"]


class TestModelsServeWithLJCalculator:
    """Integration tests for Models in serve mode with LJ calculator.

    These tests start an actual broker + worker to verify end-to-end functionality.
    """

    @pytest.fixture
    def lj_models_file(self, tmp_path):
        """Create a models.py file with a Lennard-Jones calculator."""
        models_file = tmp_path / "models.py"
        models_file.write_text("""
from mlipx import GenericASECalculator

ALL_MODELS = {
    'lj-test': GenericASECalculator(
        module='ase.calculators.lj',
        class_name='LennardJones',
    ),
}
""")
        return models_file

    @pytest.fixture
    def lj_broker_and_worker(self, tmp_path, lj_models_file):
        """Start a broker and worker with the LJ model."""
        broker_socket = tmp_path / "broker.ipc"
        workers_socket = tmp_path / "workers.ipc"
        broker_path = f"ipc://{broker_socket}"
        workers_path = f"ipc://{workers_socket}"

        # Start broker
        broker_proc = subprocess.Popen(
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

        # Wait for broker to start
        max_wait = 5.0
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if broker_socket.exists():
                break
            time.sleep(0.1)

        # Start worker - note: backend_path is the workers path, not broker path
        worker_proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"""
import sys
from pathlib import Path
sys.path.insert(0, '.')
from mlipx.serve.worker import run_worker
run_worker(
    model_name='lj-test',
    models_file=Path('{lj_models_file}'),
    backend_path='{workers_path}',
    timeout=60,
)
""",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(tmp_path.parent.parent.parent),
        )

        # Wait for worker to register - poll until model is available
        from mlipx.serve import get_broker_status

        max_wait = 10.0
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = get_broker_status(broker_path)
            if status.get("broker_running") and "lj-test" in status.get("models", []):
                break
            time.sleep(0.2)

        yield broker_path, broker_proc, worker_proc

        # Cleanup
        worker_proc.terminate()
        broker_proc.terminate()
        try:
            worker_proc.wait(timeout=5)
            broker_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
            broker_proc.kill()
            worker_proc.wait()
            broker_proc.wait()

    def test_models_serve_lists_model(self, lj_broker_and_worker):
        """Test that Models in serve mode lists the LJ model."""
        from mlipx import Models

        broker_path, _, _ = lj_broker_and_worker
        models = Models(broker=broker_path, local=False)

        assert "lj-test" in models
        assert len(models) == 1

    def test_models_serve_get_calculator(self, lj_broker_and_worker):
        """Test getting a calculator in serve mode."""
        from mlipx import Models

        broker_path, _, _ = lj_broker_and_worker
        models = Models(broker=broker_path, local=False)
        calc = models["lj-test"].get_calculator()

        assert calc is not None
        assert calc.model == "lj-test"

    def test_models_serve_compute_energy(self, lj_broker_and_worker):
        """Test computing energy via remote calculator."""
        from ase import Atoms

        from mlipx import Models

        broker_path, _, _ = lj_broker_and_worker
        models = Models(broker=broker_path, local=False)
        calc = models["lj-test"].get_calculator()

        atoms = Atoms("Ar2", positions=[[0, 0, 0], [3.0, 0, 0]])
        atoms.calc = calc

        energy = atoms.get_potential_energy()
        forces = atoms.get_forces()

        assert isinstance(energy, float)
        assert forces.shape == (2, 3)

    def test_models_serve_geometry_optimization(self, lj_broker_and_worker):
        """Test running geometry optimization via serve mode."""
        from ase import Atoms
        from ase.optimize import BFGS

        from mlipx import Models

        broker_path, _, _ = lj_broker_and_worker
        models = Models(broker=broker_path, local=False)
        calc = models["lj-test"].get_calculator()

        # Create two Ar atoms at non-equilibrium distance (too far apart)
        atoms = Atoms("Ar2", positions=[[0, 0, 0], [4.0, 0, 0]])
        atoms.calc = calc

        optimizer = BFGS(atoms, logfile=None)
        converged = optimizer.run(fmax=0.01, steps=50)

        # Should converge
        assert converged
        # Final forces should be small
        max_force = max(abs(atoms.get_forces().flatten()))
        assert max_force < 0.02
