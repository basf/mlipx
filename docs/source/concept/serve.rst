.. _serve:

Model Serving
=============

``mlipx`` provides a powerful model serving infrastructure that enables remote execution of MLIP calculations with automatic dependency management and resource scaling. The serve system is built on ZeroMQ and supports automatic worker startup, load balancing, and graceful shutdown.

.. note::

   The serve module requires additional dependencies. Install them with::

      pip install mlipx[serve]

   The serve API also requires ``uv`` for automatic dependency management. More information about ``uv`` can be found at https://docs.astral.sh/uv/

.. warning::

   UV by default uses your home directory for caching. If UV cannot link between your home directory and the current working directory, it will copy the dependencies.
   In such cases, for good performance it is crucial to set the ``UV_CACHE_DIR`` as described at https://docs.astral.sh/uv/reference/cli/#uv-cache-dir.
   You can use ``direnv`` to automatically set this variable for different mount points.

Overview
--------

The serve architecture consists of three main components:

1. **Broker**: Load balancer that routes calculation requests to available workers
2. **Workers**: Calculator instances that process requests for specific models
3. **Client**: Transparent interface that works seamlessly with existing mlipx code

Key Features
~~~~~~~~~~~~

- **Automatic Dependency Management**: Workers automatically install required dependencies using UV extras
- **Auto-scaling**: Broker can automatically start workers on demand
- **Self-terminating Workers**: Workers shutdown automatically after idle timeout
- **Load Balancing**: LRU (Least Recently Used) pattern distributes work efficiently
- **Transparent Integration**: Existing code works without modification via environment variables
- **Cross-platform Locking**: Prevents duplicate broker instances on shared systems
- **User Isolation**: Socket paths are user-specific to prevent conflicts on shared systems
- **Worker Logging**: Auto-started worker stderr is captured to log files for debugging

Quick Start
-----------

Starting the Broker with Autostart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to use serve is with the autostart broker, which automatically spawns workers on demand:

.. code-block:: console

   $ mlipx serve-broker --autostart

This will automatically discover your ``models.py`` file (see :ref:`model-discovery` below) and start workers as needed.

Workers will be started automatically when the first calculation request arrives for a model, and will shutdown after 5 minutes of inactivity (configurable with ``--worker-timeout``).

**Serve only specific models**:

.. code-block:: console

   $ mlipx serve-broker --autostart mace-mpa-0 orb-v2

This limits the broker to only serve the specified models, even if more are defined in ``models.py``.

Using Served Models
~~~~~~~~~~~~~~~~~~~

Enable serve globally via environment variable:

.. code-block:: console

   $ export MLIPX_USE_SERVE=true
   $ # Now all mlipx calculations will use served models if available

Or control it programmatically:

.. code-block:: python

   from mlipx import GenericASECalculator

   model = GenericASECalculator(
       module="mace.calculators",
       class_name="mace_mp",
       device="auto",
       serve_name="mace-mpa-0",  # Model name for serve lookups
       extra=["mace"],
   )

   # Use served model
   calc = model.get_calculator(use_serve=True)

   # Force local calculator
   calc = model.get_calculator(use_serve=False)

Checking Status
~~~~~~~~~~~~~~~

Check which models are available and how many workers are running:

.. code-block:: console

   $ mlipx serve-status


Architecture
------------

Broker
~~~~~~

The broker acts as a load balancer, routing calculation requests from clients to available workers. It implements the LRU (Least Recently Used) pattern to ensure fair load distribution.

**Starting a basic broker**:

.. code-block:: console

   $ mlipx serve-broker

**Starting with autostart** (recommended):

.. code-block:: console

   $ mlipx serve-broker --autostart --worker-timeout 600

Options:

- ``--path``: Custom IPC path for broker frontend
- ``--autostart``: Enable automatic worker startup
- ``--models``: Path to custom models.py file
- ``--worker-timeout``: Idle timeout for auto-started workers in seconds (default: 300)
- ``--worker-start-timeout``: Maximum time to wait for worker startup (default: 60)

Workers
~~~~~~~

Workers are processes that load a specific MLIP model and serve calculations. Each worker:

- Automatically installs required dependencies using UV extras
- Registers with the broker and receives calculation requests
- Sends heartbeats to maintain availability
- Shuts down after idle timeout (resets on each request)

**Manual worker startup**:

.. code-block:: console

   $ uv run mlipx serve mace-mpa-0

The command automatically detects that ``mace-mpa-0`` requires the ``mace`` extra and internally becomes:

.. code-block:: console

   $ uv run --extra mace mlipx serve mace-mpa-0 --no-uv

Options:

- ``--broker``: Custom broker backend path
- ``--models``: Path to custom models.py file
- ``--timeout``: Idle timeout in seconds (default: 300)
- ``--no-uv``: Disable UV wrapper (if already in correct environment)

.. note::

   With autostart enabled, you typically don't need to manually start workers!

Client API
~~~~~~~~~~

The client provides a transparent interface for using served models. It's integrated directly into the ``GenericASECalculator`` class.

**Environment Variable Control**:

.. code-block:: bash

   # Enable serve globally
   export MLIPX_USE_SERVE=true

   # Disable serve globally
   export MLIPX_USE_SERVE=false  # or unset

**Programmatic Control**:

.. code-block:: python

   from mlipx import GenericASECalculator

   model = GenericASECalculator(
       module="mace.calculators",
       class_name="mace_mp",
       device="auto",
       serve_name="mace-mpa-0",  # Model name for serve lookups
       extra=["mace"],
   )

   # Try served model first, fallback to local if unavailable
   calc = model.get_calculator(use_serve=True)

   # Use only local calculator
   calc = model.get_calculator(use_serve=False)

   # Use environment variable setting (default)
   calc = model.get_calculator()  # Respects MLIPX_USE_SERVE

**Using the Models API directly**:

.. code-block:: python

   from mlipx.serve import Models

   models = Models()

   # Check available models
   print(list(models))

   # Check if specific model is available
   if "mace-mpa-0" in models:
       calc = models["mace-mpa-0"].get_calculator()

.. _model-discovery:

Model Discovery
---------------

When you run ``mlipx serve-broker --autostart`` or ``mlipx serve``, mlipx automatically searches for a ``models.py`` file. This makes it easy to use project-specific model configurations without explicit ``--models`` flags.

Discovery Order
~~~~~~~~~~~~~~~

The discovery follows this priority (highest to lowest):

1. **--models flag**: Explicit path always wins
2. **MLIPX_MODELS environment variable**: For CI/shared configurations
3. **Upward search for models.py**: Searches from current directory up to root
4. **Built-in package default**: Falls back to ``mlipx/recipes/models.py.jinja2``

Upward Search
~~~~~~~~~~~~~

The upward search (like git finding ``.git``) is particularly useful for project layouts:

.. code-block:: text

   /my-project/
   ├── models.py              ← Found! (contains ALL_MODELS)
   ├── pyproject.toml
   └── recipes/
       └── md/
           └── .dvc/          ← cwd when running dvc repro

Running ``mlipx serve-broker --autostart`` from ``/my-project/recipes/md/`` will find ``/my-project/models.py``.

.. note::

   Only ``models.py`` files containing ``ALL_MODELS`` are recognized as valid mlipx model files.
   This prevents false positives from unrelated ``models.py`` files.

Using MLIPX_MODELS Environment Variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For CI/CD or shared configurations:

.. code-block:: console

   $ export MLIPX_MODELS=/shared/team-models.py
   $ mlipx serve-broker --autostart

Typical Workflow
~~~~~~~~~~~~~~~~

1. Run ``mlipx recipes`` to generate ``models.py`` in your project root
2. Run ``mlipx serve-broker --autostart`` from anywhere in the project
3. The broker automatically finds your ``models.py``

.. code-block:: console

   $ cd /my-project
   $ mlipx recipes ev --models mace-mpa-0,orb-v2 --material-ids mp-1143
   $ mlipx serve-broker --autostart
   Models file: /my-project/models.py (discovered at /my-project)
   ...

Model Configuration
-------------------

To make a model available for serving, it needs two additional fields in the model definition:

**serve_name** (str | None)
   Model identifier used for serve lookups. Auto-injected from the dictionary key in ``models.py.jinja2``.

**extra** (list[str] | None)
   List of UV extras required for this model (e.g., ``["mace"]``, ``["sevenn"]``).

Example Model Definition
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # In models.py or custom models file

   ALL_MODELS["mace-mpa-0"] = GenericASECalculator(
       module="mace.calculators",
       class_name="mace_mp",
       device="auto",
       kwargs={"model": "../../models/mace-mpa-0-medium.model"},
       extra=["mace"],  # UV extra for dependencies
       # serve_name="mace-mpa-0"  # typically auto-injected
   )

   ALL_MODELS["chgnet"] = GenericASECalculator(
       module="chgnet.model.model",
       class_name="CHGNet",
       device="auto",
       extra=["chgnet"],
   )

The ``serve_name`` field is automatically injected by the template at the end of ``models.py.jinja2``:

.. code-block:: python

   # Auto-inject model names for serve integration
   for _model_key, _model_instance in ALL_MODELS.items():
       if hasattr(_model_instance, 'serve_name') and _model_instance.serve_name is None:
           _model_instance.serve_name = _model_key

Advanced Usage
--------------

Custom Models File
~~~~~~~~~~~~~~~~~~

Use a custom models file for specialized model registries:

.. code-block:: console

   # Start broker with custom models
   $ mlipx serve-broker --autostart --models /path/to/custom-models.py

   # Start worker with custom models
   $ uv run mlipx serve my-custom-model --models /path/to/custom-models.py

Custom IPC Paths
~~~~~~~~~~~~~~~~

Specify custom IPC socket paths for multiple broker instances:

.. code-block:: console

   # Start broker on custom path
   $ mlipx serve-broker --path ipc:///tmp/my-broker.ipc

   # Start worker connecting to custom broker
   $ uv run mlipx serve mace-mpa-0 --broker ipc:///tmp/my-broker-workers.ipc

   # Check status of custom broker
   $ mlipx serve-status --broker ipc:///tmp/my-broker.ipc

Multiple Workers per Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

Start multiple workers for the same model to enable parallel processing:

.. code-block:: console

   $ uv run mlipx serve mace-mpa-0 &
   $ uv run mlipx serve mace-mpa-0 &
   $ uv run mlipx serve mace-mpa-0 &

The broker will distribute requests across all available workers using LRU scheduling.

DVC Integration
~~~~~~~~~~~~~~~

Use serve transparently with DVC workflows:

.. code-block:: console

   # Start broker with autostart
   $ mlipx serve-broker --autostart &

   # Enable serve globally
   $ export MLIPX_USE_SERVE=true

   # Run DVC pipeline - automatically uses served models!
   $ dvc repro

All model calculations will now use the serve infrastructure, with workers starting automatically as needed.

Troubleshooting
---------------

Worker Logs
~~~~~~~~~~~

When using the autostart broker, worker stderr is captured to log files for debugging. Logs are stored in:

- **Linux/macOS**: ``/tmp/mlipx/worker_logs/<model>-<timestamp>.log``
- **Windows**: ``%TEMP%/mlipx/worker_logs/<model>-<timestamp>.log``

Check these logs if a worker fails to start or encounters errors during calculation.

Broker Already Running
~~~~~~~~~~~~~~~~~~~~~~

If you see "Another broker is already running", it means a broker is already active on the same socket path. Either:

1. Use the existing broker
2. Stop the existing broker and start a new one
3. Use a different ``--path`` for a separate broker instance

Socket Path Conflicts on Shared Systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On shared systems (e.g., HPC clusters), socket paths are automatically isolated by username:

- With ``XDG_RUNTIME_DIR``: ``/run/user/<uid>/mlipx/broker.ipc``
- Fallback: ``/tmp/mlipx-<username>/broker.ipc``

This prevents conflicts between different users on the same machine.

Checking Broker Status
~~~~~~~~~~~~~~~~~~~~~~

Use ``mlipx serve-status`` to diagnose issues:

.. code-block:: console

   $ mlipx serve-status

This shows:

- Whether the broker is running
- Which models have active workers
- Number of workers per model
- Available models for autostart (if enabled)
