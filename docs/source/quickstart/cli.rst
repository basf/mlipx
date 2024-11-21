Command Line Interface
======================

This guide will help you get started with ``mlipx`` by creating a new project in an empty directory and computing metrics for a machine-learned interatomic potential (MLIP) against reference DFT data.

First, create a new project directory and initialize it with Git and DVC:

.. code-block:: bash

    (.venv) $ mkdir my_project
    (.venv) $ cd my_project
    (.venv) $ git init
    (.venv) $ dvc init

Adding Reference Data
----------------------
Next, add a reference DFT dataset to the project. For this example, we use a slice from the mptraj dataset :footcite:`dengCHGNetPretrainedUniversal2023`.

.. note::

    If you have your own data, replace this file with any dataset that can be read by ``ase.io.read`` and includes reference energies and forces.

.. code-block:: bash

    (.venv) $ dvc import-url https://github.com/zincware/ips-mace/releases/download/v0.1.0/mptraj_slice.xyz mptraj_slice.xyz

Adding the Recipe
-----------------
With the reference data in place, add a ``mlipx`` recipe to compute metrics:

.. code-block:: bash

    (.venv) $ mlipx recipes metrics --datapath mptraj_slice.xyz

This command generates a ``main.py`` file in the current directory, which defines the workflow for the recipe.

Defining Models
---------------
Define the models to evaluate. For simplicity, this example uses the MACE-MP-0 model :footcite:`batatiaFoundationModelAtomistic2023`.

Create a file named ``models.py`` in the current directory with the following content:

.. code-block:: python

    import mlipx

    mace_mp = mlipx.GenericASECalculator(
        module="mace.calculators",
        class_name="mace_mp",
        device="auto",
        kwargs={
            "model": "medium",
        },
    )

    MODELS = {"mace_mp": mace_mp}

Running the Workflow
---------------------
Now, run the workflow using the following commands:

.. code-block:: bash

    (.venv) $ python main.py
    (.venv) $ dvc repro

Listing Steps and Visualizing Results
-------------------------------------
To explore the available steps and visualize results, use the commands below:

.. code-block:: bash

    (.venv) $ zntrack list
    (.venv) $ mlipx compare mace_mp_CompareCalculatorResults

.. note::

    To use ``mlipx compare``, you must have an active ZnDraw server running. Provide the server URL via the ``--zndraw_url`` argument or the ``ZNDRAW_URL`` environment variable.

    You can start a server locally with the command ``zndraw`` in a separate terminal or use the public server at https://zndraw.icp.uni-stuttgart.de.

.. footbibliography::
