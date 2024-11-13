Workflows
=========

The :code:`mlipx` package is based ZnTrack.
Although, :code:`mlipx` usage does not require you to understand how ZnTrack works, the following will give a short overview of the concept.
We will take an example of building a simulation Box from :code:`smiles` as illustrated in the following Python script.

.. code:: python

    import rdkit2ase

    water = rdkit2ase.smiles2atoms('O')
    ethanol = rdkit2ase.smiles2atoms('CCO')

    box = rdkit2ase.pack([[water], [ethanol]], counts=[50, 50], density=800)
    print(box)
    >>> ase.Atoms(...)

This script can also be represented as the following workflow which we will now convert.

.. mermaid::
    :align: center

    graph TD
        BuildWater --> PackBox
        BuildEtOH --> PackBox


With ZnTrack you can build complex workflows based on :term:`DVC` and :term:`GIT`.
The first part of a workflow is defining the steps, which in the context of ZnTrack are called :code:`Node`.
A :code:`Node` is based on the Python :code:`dataclass` module defining it's arguments as class attributes.

.. note::

    It is highly recommend to follow the single-responsibility principle when writing a :code:`Node`. For example if you have a relaxation followed by a molecular dynamics simulation, separate the these into two Nodes. But also keep it mind, that there is some communication overhead between Nodes, so e.g. defining each MD step as a separate Node would not be recommended.

.. code:: python

    import zntrack
    import ase
    import rdkit2ase

    class BuildMolecule(zntrack.Node):
        smiles: str = zntrack.params()

        frames: list[ase.Atoms] = zntrack.outs()

        def run(self):
            self.frames = [rdkit2ase.smiles2atoms(self.smiles)]

With this :code:`BuildMolecule` class we can bring the :code:`rdkit2ase.smiles2atoms` onto the graph by defining the inputs and outputs.
Further, we need to define a :code:`Node` for the :code:`rdkit2ase.pack` function.
For this, we define the :code:`PackBox` node as follows:

.. code:: python

    import ase.io
    import pathlib

    class PackBox(zntrack.Node):
        data: list[list[ase.Atoms]] = zntrack.deps()
        counts: list[int] = zntrack.params()
        density: float = zntrack.params()

        frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / 'frames.xyz')

        def run(self):
            box = rdkit2ase.pack(self.data, counts=self.counts, density=self.density)
            ase.io.write(self.frames_path, box)

.. note::

    The :code:`zntrack.outs_path(zntrack.nwd / 'frames.xyz')` provides a unique output path per node in the node working directory (nwd). It is crucial to define every input and output as ZnTrack attributes. Otherwise, the results will be lost.

With this Node, we can build our graph:

.. code:: python

    project = zntrack.Project()

    with project:
        water = BuildMolecule(smiles="O")
        ethanol = BuildMolecule(smiles="CCO")

        box = PackBox(data=[water.frames, ethanol.frames], counts=[50, 50], density=800)

    project.build()

.. note::

    The `project.build()` command will not run the graph but only define how the graph is to be executed in the future.
    Consider it a pure graph definition file.
    If you write this into a single :code:`main.py` file, it should look like

    .. dropdown:: Content of :code:`main.py`

      .. code-block:: python

        import zntrack
        import ase.io
        import rdkit2ase
        import pathlib

        class BuildMolecule(zntrack.Node):
            smiles: str = zntrack.params()

            frames: list[ase.Atoms] = zntrack.outs()

            def run(self):
                self.frames = [rdkit2ase.smiles2atoms(self.smiles)]

        class PackBox(zntrack.Node):
            data: list[list[ase.Atoms]] = zntrack.deps()
            counts: list[int] = zntrack.params()
            density: float = zntrack.params()

            frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / 'frames.xyz')

            def run(self):
                box = rdkit2ase.pack(self.data, counts=self.counts, density=self.density)
                ase.io.write(self.frames_path, box)

        if __name__ == "__main__":
            project = zntrack.Project()

            with project:
                water = BuildMolecule(smiles="O")
                ethanol = BuildMolecule(smiles="CCO")

                box = PackBox(data=[water.frames, ethanol.frames], counts=[50, 50], density=800)

            project.build()

To run the graph you can use the :term:`DVC` CLI :code:`dvc repro` (or the :term:`paraffin` package, see :ref:`Distributed evaluation`. )

Once finished, you can look at the results by loading the nodes:

.. code:: python

    import zntrack
    import ase.io

    box = zntrack.from_rev("PackBox")
    print(ase.io.read(box.frames_path))
    >>> ase.Atoms(...)


For further information have a look at the ZnTrack documentation https://zntrack.readthedocs.io and repository https://github.com/zincware/zntrack .
