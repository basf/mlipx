.. _serve:

Model Serving
=============

``mlipx`` provides model serving infrastructure using `aserpc <https://github.com/zincware/aserpc>`_, a lightweight RPC framework for serving ASE calculators over ZeroMQ. This enables remote execution of MLIP calculations with automatic dependency management and load balancing.

.. note::

   The serve API requires ``uv`` for automatic dependency management when spawning workers.
   More information about ``uv`` can be found at https://docs.astral.sh/uv/

Overview
--------

The serve architecture consists of three main components:

1. **Broker**: Load balancer that routes calculation requests to available workers
2. **Workers**: Calculator instances that process requests for specific models
3. **Client**: Transparent interface using ``aserpc.RemoteCalculator`` or the ``mlipx.Models`` class

Key Features
~~~~~~~~~~~~

- **Built on aserpc**: Uses the dedicated aserpc RPC framework for ASE calculators
- **Entry Point Discovery**: Calculators are discovered via Python entry points
- **Automatic Dependency Management**: Workers can be started with smart UV/UVX dependency resolution
- **Load Balancing**: LRU (Least Recently Used) pattern distributes work efficiently
- **Transparent Integration**: The ``Models`` class auto-detects serve vs local mode

Quick Start
-----------

Autostart Mode (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the broker with on-demand worker spawning:

.. code-block:: console

   (.venv) $ mlipx serve-broker --autostart

This will:

1. Start the aserpc broker
2. Start the aserpc manager (discovers spawn configs from mlipx entry points)
3. Workers are spawned **on-demand** when a client requests a model
4. Workers auto-shutdown after idle timeout (default: 300s)

The manager uses spawn configurations registered via the ``aserpc.spawn`` entry point.
Each model has a pre-configured command that uses ``uv run`` or ``uvx`` with the
correct dependencies.

Starting the Broker
~~~~~~~~~~~~~~~~~~~

Start the aserpc broker without autostart:

.. code-block:: console

   (.venv) $ mlipx serve-broker
   # or directly:
   (.venv) $ aserpc broker

Starting Workers
~~~~~~~~~~~~~~~~

Start a worker for a specific model:

.. code-block:: console

   (.venv) $ mlipx serve mace-mpa-0
   # or directly:
   (.venv) $ aserpc worker mace-mpa-0

The ``mlipx serve`` command provides smart dependency resolution:

- If the model's extras are available in your local project, uses ``uv run --extra``
- Otherwise, uses ``uvx --from mlipx[extras]`` to install from the mlipx package

Using Served Models
~~~~~~~~~~~~~~~~~~~

Use the ``Models`` class for a unified interface:

.. code-block:: python

   from mlipx import Models

   # Auto-detects serve vs local mode
   models = Models()

   # List available models
   print(list(models))

   # Get a calculator (uses aserpc.RemoteCalculator in serve mode)
   calc = models["mace-mpa-0"].get_calculator()

Or use ``aserpc.RemoteCalculator`` directly:

.. code-block:: python

   from aserpc import RemoteCalculator
   from ase.build import molecule

   water = molecule("H2O")
   water.calc = RemoteCalculator("mace-mpa-0")
   energy = water.get_potential_energy()

Checking Status
~~~~~~~~~~~~~~~

Check which models have active workers:

.. code-block:: console

   (.venv) $ mlipx serve-status

List available calculators registered via entry points:

.. code-block:: console

   (.venv) $ aserpc list

Shutting Down
~~~~~~~~~~~~~

Shutdown all workers:

.. code-block:: console

   (.venv) $ mlipx serve-status --shutdown

Architecture
------------

Broker
~~~~~~

The broker acts as a load balancer, routing calculation requests from clients to available workers.

**Starting the broker**:

.. code-block:: console

   (.venv) $ mlipx serve-broker
   # With custom options:
   (.venv) $ mlipx serve-broker --timeout 60.0 --log-level DEBUG

Options:

- ``--frontend``: Custom IPC path for broker frontend (clients connect here)
- ``--backend``: Custom IPC path for broker backend (workers connect here)
- ``--timeout``: Worker timeout in seconds (default: 30.0)
- ``--queue-timeout``: Request queue timeout in seconds (default: 60.0)
- ``--log-level``: Log level (default: INFO)
- ``--autostart``: Enable on-demand worker spawning via manager

Workers
~~~~~~~

Workers are processes that load a specific MLIP calculator and serve calculations. Each worker:

- Registers with the broker via entry points
- Sends heartbeats to maintain availability
- Shuts down after idle timeout

**Starting workers with mlipx**:

.. code-block:: console

   (.venv) $ mlipx serve mace-mpa-0 --idle-timeout 600

**Starting workers directly with aserpc**:

.. code-block:: console

   (.venv) $ aserpc worker mace-mpa-0 --idle-timeout 600

Options (mlipx serve):

- ``--broker``: Custom broker backend path
- ``--idle-timeout``: Idle timeout in seconds (default: 300)
- ``--heartbeat``: Heartbeat interval in seconds (default: 5.0)
- ``--log-level``: Log level (default: INFO)

Calculator Entry Points
-----------------------

mlipx registers its calculators via Python entry points. This allows ``aserpc`` to discover available calculators automatically.

The entry point is defined in ``pyproject.toml``:

.. code-block:: toml

   [project.entry-points.'aserpc.calculators']
   mlipx = 'mlipx.aserpc:get_calculators'

The ``get_calculators()`` function returns metadata for available calculators:

.. code-block:: python

   def get_calculators() -> dict[str, dict]:
       """Return metadata for available calculators."""
       calcs = {}

       # Check if mace is installed
       if importlib.util.find_spec("mace") is not None:
           calcs["mace-mpa-0"] = {
               "factory": "mace.calculators:mace_mp",
           }

       # Check if chgnet is installed
       if importlib.util.find_spec("chgnet") is not None:
           calcs["chgnet"] = {"factory": "chgnet.model:CHGNetCalculator"}

       return calcs

This approach:

- Uses ``importlib.util.find_spec()`` for lightweight package detection without importing
- Supports ``factory`` (module:class) and ``factory_fn`` (callable) patterns
- Allows optional ``kwargs`` for calculator initialization

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

aserpc can be configured via environment variables:

.. code-block:: bash

   export ASERPC_IPC_DIR=/tmp/aserpc
   export ASERPC_WORKER_TIMEOUT=30.0
   export ASERPC_HEARTBEAT_INTERVAL=5.0
   export ASERPC_IDLE_TIMEOUT=300.0
   export ASERPC_REQUEST_QUEUE_TIMEOUT=60.0
   export ASERPC_CLIENT_TIMEOUT_MS=60000

pyproject.toml Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [tool.aserpc]
   ipc_dir = "/tmp/aserpc"
   worker_timeout = 30.0
   heartbeat_interval = 5.0
   idle_timeout = 300.0
   request_queue_timeout = 60.0
   client_timeout_ms = 60000

The Models Class
----------------

The ``Models`` class provides a unified interface that works in both local and serve modes:

.. code-block:: python

   from mlipx import Models

   # Auto-detect mode (serve if broker running, else local)
   models = Models()

   # Force local mode
   models = Models(local=True)

   # Force serve mode
   models = Models(local=False)

   # With custom timeout (milliseconds) for serve mode
   models = Models(timeout=60000)

   # Access models
   calc = models["mace-mpa-0"].get_calculator()

Parameters:

- ``path``: Path to models.py file (for local mode). If None, uses discovery.
- ``timeout``: Timeout in milliseconds for serve mode. If None, uses aserpc defaults.
- ``local``: Force local mode (True), force serve mode (False), or auto-detect (None).

Properties and Methods:

- ``models.mode``: Returns current mode ('local' or 'serve')
- ``models.refresh()``: Refresh model list from broker (serve mode only)

In serve mode, it uses ``aserpc.RemoteCalculator`` under the hood.
In local mode, it loads models from a ``models.py`` file.

Scale-to-Zero with Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~

The aserpc Manager enables automatic worker spawning on demand. When using
``mlipx serve-broker --autostart``, workers are only started when a client
requests a model, and they automatically shut down after an idle timeout.

**How it works:**

1. Client requests a calculator (e.g., ``mace-mpa-0``)
2. Broker checks if a worker is available
3. If not, broker sends SPAWN_REQUEST to manager
4. Manager spawns worker using pre-configured command
5. Worker registers with broker and handles the request
6. Worker shuts down after idle timeout (default: 300s)

**Spawn configurations** are registered via entry points in ``pyproject.toml``:

.. code-block:: toml

   [project.entry-points."aserpc.spawn"]
   mlipx = "mlipx.aserpc:get_spawn_configs"

Each spawn config specifies how to start a worker with the correct dependencies:

- Uses ``uv run --extra <dep>`` if extras are in local ``pyproject.toml``
- Uses ``uvx --from mlipx[<dep>]`` otherwise (installs from PyPI)

Model Discovery (Local Mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using local mode, mlipx searches for a ``models.py`` file:

1. **--models flag / path parameter**: Explicit path always wins
2. **MLIPX_MODELS environment variable**: For CI/shared configurations
3. **Upward search for models.py**: Searches from current directory up to root
4. **Built-in package default**: Falls back to ``mlipx/recipes/models.py.jinja2``

Advanced Usage
--------------

Multiple Workers per Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

Start multiple workers for the same model to enable parallel processing:

.. code-block:: console

   (.venv) $ mlipx serve mace-mpa-0 &
   (.venv) $ mlipx serve mace-mpa-0 &
   (.venv) $ mlipx serve mace-mpa-0 &

The broker will distribute requests across all available workers using LRU scheduling.

Custom IPC Paths
~~~~~~~~~~~~~~~~

Specify custom IPC socket paths:

.. code-block:: console

   # Start broker on custom path
   (.venv) $ mlipx serve-broker --frontend ipc:///tmp/my-frontend.ipc --backend ipc:///tmp/my-backend.ipc

   # Start worker connecting to custom broker
   (.venv) $ mlipx serve mace-mpa-0 --broker ipc:///tmp/my-backend.ipc

DVC Integration
~~~~~~~~~~~~~~~

Use serve with DVC workflows:

.. code-block:: console

   # Start broker
   (.venv) $ aserpc broker &

   # Start workers
   (.venv) $ aserpc worker mace-mpa-0 &

   # Run DVC pipeline
   (.venv) $ dvc repro

Troubleshooting
---------------

Checking Broker Status
~~~~~~~~~~~~~~~~~~~~~~

Use ``mlipx serve-status`` to diagnose issues:

.. code-block:: console

   (.venv) $ mlipx serve-status

This shows:

- Whether the broker is running
- Which models have active workers
- Number of workers per model

Listing Available Calculators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List all calculators registered via entry points:

.. code-block:: console

   (.venv) $ aserpc list

This shows calculators from all packages that provide the ``aserpc.calculators`` entry point.
