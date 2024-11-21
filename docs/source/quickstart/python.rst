Python Interface
================

In the :ref:`cli-quickstart` guide, we used the CLI to compute metrics for an MLIP against reference DFT data.
Now we will show you how to achieve the same result using the Python interface.

First, create a new project directory and initialize it with Git and DVC as before:

.. code-block:: bash

    (.venv) $ mkdir my_project
    (.venv) $ cd my_project
    (.venv) $ git init
    (.venv) $ dvc init



Adding Reference Data
----------------------

Create a new Python file named ``main.py`` in the project directory with the following content:

.. code-block:: python

    import mlipx
    import zntrack

    data = zntrack.add(
        url="https://github.com/zincware/ips-mace/releases/download/v0.1.0/mptraj_slice.xyz",
        path="mptraj_slice.xyz",
    )


This will download the reference data to the project directory.


Defining Models
---------------

Next, define the models to evaluate.
Therefore add the following code to the ``main.py`` file:

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

Next, add a recipe to compute metrics for the MLIP.
Add to the ``main.py`` file:

.. code-block:: python

    project = mlipx.Project()


    with project.group("reference"):
        data = mlipx.LoadDataFile(path=data)
        ref_evaluation = mlipx.EvaluateCalculatorResults(data=data.frames)

    with project.group("mace-mp"):
        updated_data = mlipx.ApplyCalculator(data=data.frames, model=mace_mp)
        evaluation = mlipx.EvaluateCalculatorResults(data=updated_data.frames)
        mlipx.CompareCalculatorResults(data=evaluation, reference=ref_evaluation)

    project.repro()

Running the Workflow
---------------------

Finally, run the workflow by executing the ``main.py`` file:

.. note::

    If you want to execute the workflow using ``dvc repro``, replace ``project.repro()`` with ``project.build()`` in the ``main.py`` file.

.. code-block:: bash

    (.venv) $ python main.py

This will compute the metrics for the MLIP against the reference DFT data.


Listing Steps and Visualizing Results
-------------------------------------
As before, to explore the available steps and visualize results, use the commands below:

.. code-block:: bash

    (.venv) $ zntrack list
    (.venv) $ mlipx compare mace_mp_CompareCalculatorResults
