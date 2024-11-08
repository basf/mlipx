Recipes
=======

Setup
-----
One of :code:`mlipx` core functionality is providing you with pre-designed recipes.
These define workflows for evaluating :term:`MLIP` on specific tasks.
You can get an overview of all available recipes using

.. code-block:: console

   (.venv) $ mlipx recipes --help

All recipes follow the same structure.
It is recommended, to create a new directory for each recipe.

.. code-block:: console

   (.venv) $ mkdir molecular_dynamics
   (.venv) $ cd molecular_dynamics
   (.venv) $ mlipx recipes md --initialize

This will create the following structure:

.. code-block:: console

   molecular_dynamics/
   ├── .git/
   ├── .dvc/
   ├── models.py
   └── main.py

After initialization, adapt the :code:`main.py` file to point towards the requested data files.
Define all models for testing in the :term:`models.py` file.

Finally, build the recipe using

.. code-block:: console

   (.venv) $ python main.py
   (.venv) $ dvc repro


Datasets
--------
All recipes come with a predefined dataset section.
In this case, the raw data is provided e.g. via :code:`DATAPATH = "traj.xyz"`.

.. dropdown::  Local data file (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      import mlipx

      DATAPATH = "..."

      project = zntrack.Project()

      with project.group("initialize"):
         data = mlipx.LoadDataFile(path=DATAPATH)

We can replace this local datafile with a remote dataset, allowing us for example to evaluate the :code:`mptraj` dataset.
Often, this is combined with a filtering step, to select only relevant configurations.
Here we select all structures containing :code:`F` and :code:`B` atoms.

.. dropdown:: Importing online resources (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      import mlipx

      mptraj = zntrack.add(
         url="https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b/mp_traj_combined.xyz",
         path="mptraj.xyz",
      )

      with project:
         raw_data = mlipx.LoadDataFile(path=mptraj, stop=2)
         data = mlipx.FilterAtoms(data=data.frames, elements=["B", "F"])

A third approach is generating data on the fly.
Within :code:`mlipx` this can be used to build molecules or simulation boxes from smiles.
Here we generate a simulation box consisting of 10 ethanol molecules.

.. dropdown:: Using SMILES (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      from models import MODELS

      import mlipx

      project = zntrack.Project()

      with project.group("initialize"):
         confs = mlipx.Smiles2Conformers(smiles="CCO", num_confs=10)
         data = mlipx.BuildBox(data=[confs.frames], counts=[10], density=789)

.. note::
   The :code:`BuildBox` node requires :term:`Packmol` to be installed.
   If you do not need a simulation box, you can also use :code:`confs.frames` directly.


This is described with an example for :ref:`Energy Volume Curves`.


Models
------
For each recipe, the models to evaluate are defined in the :term:`models.py` file.
Most of the time :code:`mlipx.GenericASECalculator` can be used to access models.
Sometimes, a custom calculator has to be provided.
In the following we will show how to write a custom calculator node for :code:`SevenCalc`.
This is just an example, as the :code:`SevenCalc` could also be used with :code:`mlipx.GenericASECalculator`.

.. dropdown:: Content of :code:`models.py`
   :open:

   .. code-block:: python

      import mlipx
      from src import SevenCalc


      mace_medium = mlipx.GenericASECalculator(
         module="mace.calculators",
         class_name="MACECalculator",
         device='auto',
         kwargs={
            "model_paths": "mace_models/y7uhwpje-medium.model",
         },
      )

      mace_agnesi = mlipx.GenericASECalculator(
         module="mace.calculators",
         class_name="MACECalculator",
         device='auto',
         kwargs={
            "model_paths": "mace_models/mace_mp_agnesi_medium.model",
         },
      )

      sevennet = SevenCalc(model='7net-0')

      MODELS = {
         "mace_medm": mace_medium,
         "mace_agne": mace_agnesi,
         "7net": sevennet,
      }

Where the :code:`SevenCalc` is defined in :code:`src/__init__.py` as follows:

.. dropdown:: Content of :code:`src/__init__.py`
   :open:

   .. code-block:: python

      import dataclasses
      from ase.calculators.calculator import Calculator


      @dataclasses.dataclass
      class SevenCalc:
         model: str

         def get_calculator(self, **kwargs) -> Calculator:
            from sevenn.sevennet_calculator import SevenNetCalculator
            sevennet= SevenNetCalculator(self.model, device='cpu')

            return sevennet

More information on can be found in the :ref:`custom_nodes` section.


Upload Results
--------------
Once the recipe is finished, you can persist the results and upload them to a remote storage.
Therefore, you want to make a GIT commit and push it to your repository.

.. code-block:: console

   (.venv) $ git add .
   (.venv) $ git commit -m "Finished molecular dynamics test"
   (.venv) $ git push
   (.venv) $ dvc push

.. note::
   You need to define a :term:`GIT` and :term:`DVC` remote to push the results.
   More information on how to setup a :term:`DVC` remote can be found at https://dvc.org/doc/user-guide/data-management/remote-storage.


In combination or as an alternative, you can upload the results to a parameter and metric tracking service, such as :term:`mlflow`.
Given a running :term:`mlflow` server, you can use the following command to upload the results:

.. code-block:: console

   (.venv) $ zntrack mlflow-sync --help

.. note::
   Depending on the installed packages, the :term:`mlflow` command might not be available.
   This functionality is provided by the :term:`zntrack` package, and other tracking services can be used as well.
   They will show up once the respective package is installed.
   See https://zntrack.readthedocs.io/ for more information.


Overview
--------

.. toctree::
   recipes/md
   recipes/relax
   recipes/neb
   recipes/phase_diagram
   recipes/pourbaix_diagram
   recipes/vibrational_analysis
   recipes/energy_and_forces
   recipes/homonuclear_diatomics
   recipes/energy_volume
