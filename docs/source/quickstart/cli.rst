Command Line Interface
=======================

To start with ``mlipx`` we will create a project in a new and empty directory and compute metrics for one MLIP with respect to reference DFT data..

.. code-block:: bash

    (.venv) $ mkdir my_project
    (.venv) $ cd my_project
    (.venv) $ git init
    (.venv) $ dvc init

Now we can add a reference DFT data set to the project.
We will use a slice from the mptraj :footcite:`dengCHGNetPretrainedUniversal2023` dataset as an example.
To use your own data, replace this file with any other file that can be read by ``ase.io.read`` and includes reference energies and forces.

.. code-block:: bash

    (.venv) $ dvc import-url https://github.com/zincware/ips-mace/releases/download/v0.1.0/mptraj_slice.xyz mptraj_slice.xyz

Now with the reference data in place, we can add the ``mlipx`` recipe.

.. code-block:: bash

    (.venv) $ mlipx recipes metrics --datapath mptraj_slice.xyz


This will create a file ``main.py`` in the current directory that defines the workflow for the recipe.

Finally, we need to define the models that we want to evaluate.
For simplicity, we will only use one model, the MACE-MP-
0 model :footcite:`batatiaFoundationModelAtomistic2023`.

Therefore, we will create the following file ``models.py`` in the current directory.

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


with the models in place, we can now run the workflow.

.. code-block:: bash

    (.venv) $ python main.py
    (.venv) $ dvc repro


Now we can list the available steps and visualize the results.

.. code-block:: bash

    (.venv) $ zntrack list
    (.venv) $ mlipx compare mace_mp_CompareCalculatorResults


.. note::

    To use ``mlipx compare`` you need to have an active zndraw server running and provide either the ``--zndraw_url`` argument or set the environment variable ``ZNDRAW_URL``.
    You can start a server locally by running ``zndraw`` in a separate terminal or use the public server at https://zndraw.icp.uni-stuttgart.de.


.. footbibliography::
