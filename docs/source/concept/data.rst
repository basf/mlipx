Datasets
========
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
         raw_data = mlipx.LoadDataFile(path=mptraj)
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
