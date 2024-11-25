.. _python-quickstart:

Python Interface
================

In the :ref:`cli-quickstart` guide, we demonstrated how to compute metrics for an MLIP against reference DFT data using the CLI.
This guide shows how to achieve the same result using the Python interface.

Getting Started
---------------

First, create a new project directory and initialize it with Git and DVC, as shown below:

.. code-block:: console

    (.venv) $ mkdir my_project
    (.venv) $ cd my_project
    (.venv) $ git init
    (.venv) $ dvc init

Adding Reference Data
----------------------

Create a new Python file named ``main.py`` in the project directory, and add the following code to download the reference dataset:

.. code-block:: python

    import mlipx
    import zntrack

    mptraj = zntrack.add(
        url="https://github.com/zincware/ips-mace/releases/download/v0.1.0/mptraj_slice.xyz",
        path="data.xyz",
    )

This will download the reference data file ``mptraj_slice.xyz`` into your project directory.

Defining Models
---------------

Define the MLIP models to evaluate by adding the following code to the ``main.py`` file:

.. code-block:: python

    mace_mp = mlipx.GenericASECalculator(
        module="mace.calculators",
        class_name="mace_mp",
        device="auto",
        kwargs={
            "model": "medium",
        },
    )

Adding the Recipe
-----------------

Next, set up the recipe to compute metrics for the MLIP. Add the following code to the ``main.py`` file:

.. code-block:: python

    project = mlipx.Project()

    with project.group("reference"):
        data = mlipx.LoadDataFile(path=mptraj)
        ref_evaluation = mlipx.EvaluateCalculatorResults(data=data.frames)

    with project.group("mace-mp"):
        updated_data = mlipx.ApplyCalculator(data=data.frames, model=mace_mp)
        evaluation = mlipx.EvaluateCalculatorResults(data=updated_data.frames)
        mlipx.CompareCalculatorResults(data=evaluation, reference=ref_evaluation)

    project.repro()

Running the Workflow
---------------------

Finally, run the workflow by executing the ``main.py`` file:

.. code-block:: console

    (.venv) $ python main.py

.. note::

    If you want to execute the workflow using ``dvc repro``, replace ``project.repro()`` with ``project.build()`` in the ``main.py`` file.

This will compute the metrics for the MLIP against the reference DFT data.

Listing Steps and Visualizing Results
-------------------------------------

As with the CLI approach, you can list the available steps and visualize results using the following commands:

.. code-block:: console

    (.venv) $ zntrack list
    (.venv) $ mlipx compare mace_mp_CompareCalculatorResults

Alternatively, you can load the results for this and any other Node directly into a Python kernel using the following code:

.. code-block:: python

    import zntrack

    node = zntrack.from_rev("mace_mp_CompareCalculatorResults")
    print(node.figures)
    >>> {"fmax_error": plotly.graph_objects.Figure(), ...}
