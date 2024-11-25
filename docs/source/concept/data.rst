.. _data:

Datasets
========
Data within ``mlipx`` is always represented as a list of :term:`ASE` atoms objects.
Nevertheless, there are different ways to provide this data to the workflow.

Local Data Files
----------------
You can simply provide a local data file, e.g. a trajectory file to the workflow.

.. code:: console

   (.venv) $ cp /path/to/data.xyz .
   (.venv) $ dvc add data.xyz

.. dropdown::  Local data file (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      import mlipx

      DATAPATH = "data.xyz"

      project = zntrack.Project()

      with project.group("initialize"):
         data = mlipx.LoadDataFile(path=DATAPATH)

Remote Data Files
-----------------
As ``mlipx`` uses :term:`DVC` we can easily import data from a remote location.
You can do so by importing the file manually:

.. code:: console

   (.venv) $ dvc import-url https://url/to/your/data.xyz data.xyz

or by using the :code:`zntrack` interface:

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
         raw_data = mlipx.LoadDataFile(path=mptraj)
         data = mlipx.FilterAtoms(data=data.frames, elements=["B", "F"])


Materials Project
-----------------
We can also search the ``Materials Project`` for structures.

.. code:: python

   import mlipx

   project = mlipx.Project()

   with project.group("initialize"):
        data = mlipx.MPRester(search_kwargs={"material_ids": ["mp-1143"]})

.. note::
   This requires an API key from the Materials Project.
   You need to set the environment variable :code:`MP_API_KEY` to your API key.


Generating Data
--------------

Another approach is generating data on the fly.
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
   The :code:`BuildBox` node requires :term:`Packmol` and :term:`rdkit2ase` to be installed.
   If you do not need a simulation box, you can also use :code:`confs.frames` directly.
