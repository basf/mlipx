.. _data:

Datasets
========

Data within ``mlipx`` is always represented as a list of :term:`ASE` atoms objects.
There are various ways to provide this data to the workflow, depending on your requirements.

Local Data Files
----------------

The simplest way to use data in the workflow is by providing a local data file, such as a trajectory file.

.. code:: console

   (.venv) $ cp /path/to/data.xyz .
   (.venv) $ dvc add data.xyz

.. dropdown:: Local data file (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      import mlipx

      DATAPATH = "data.xyz"

      project = mlipx.Project()

      with project.group("initialize"):
         data = mlipx.LoadDataFile(path=DATAPATH)

Remote Data Files
-----------------

Since ``mlipx`` integrates with :term:`DVC`, it can easily handle data from remote locations.
You can manually import a remote file:

.. code:: console

   (.venv) $ dvc import-url https://url/to/your/data.xyz data.xyz

Alternatively, you can use the ``zntrack`` interface for automated management.
This allows evaluation of datasets such as :code:`mptraj` and supports filtering to select relevant configurations.
For example, the following code selects all structures containing :code:`F` and :code:`B` atoms.

.. dropdown:: Importing online resources (:code:`main.py`)
   :open:

   .. code:: python

      import zntrack
      import mlipx

      mptraj = zntrack.add(
         url="https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b/mp_traj_combined.xyz",
         path="mptraj.xyz",
      )

      project = mlipx.Project()

      with project:
         raw_data = mlipx.LoadDataFile(path=mptraj)
         data = mlipx.FilterAtoms(data=raw_data.frames, elements=["B", "F"])

Materials Project
-----------------

You can also search and retrieve structures from the `Materials Project`.

.. dropdown:: Querying Materials Project (:code:`main.py`)
   :open:

   .. code:: python

      import mlipx

      project = mlipx.Project()

      with project.group("initialize"):
         data = mlipx.MPRester(search_kwargs={"material_ids": ["mp-1143"]})

.. note::
   To use the Materials Project, you need an API key. Set the environment variable
   :code:`MP_API_KEY` to your API key.

Generating Data
---------------

Another approach is generating data dynamically. In ``mlipx``, you can build molecules or simulation boxes from SMILES strings.
For instance, the following code generates a simulation box containing 10 ethanol molecules:

.. dropdown:: Using SMILES (:code:`main.py`)
   :open:

   .. code:: python

      import mlipx

      project = mlipx.Project()

      with project.group("initialize"):
         confs = mlipx.Smiles2Conformers(smiles="CCO", num_confs=10)
         data = mlipx.BuildBox(data=[confs.frames], counts=[10], density=789)

.. note::
   The :code:`BuildBox` node requires :term:`Packmol` and :term:`rdkit2ase`.
   If you do not need a simulation box, you can use :code:`confs.frames` directly.
