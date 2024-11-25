Glossary
========

.. glossary::

    MLIP
        Machine learned interatomic potential.

    GIT
        GIT is a distributed version control system. It allows multiple people to work on a project at the same time without overwriting each other's changes. It also keeps a history of all changes made to the project, so you can easily revert to an earlier version if necessary.

    DVC
        Data Version Control (DVC) is a tool used in machine learning projects to track and version the datasets used in the project, as well as the code and the results. This makes it easier to reproduce experiments and share results with others.
        More information can be found at https://dvc.org/ .

    mlflow
        Mlflow is an open-source platform that helps manage the machine learning lifecycle, including experimentation, reproducibility, and deployment. It keeps track of the parameters used in the model as well as the metrics obtained from the model.
        More information can be found at https://mlflow.org/ .

    ZnTrack
        ZnTrack :footcite:t:`zillsZnTrackDataCode2024` is a Python package that provides a framework for defining and executing workflows. It allows users to define a sequence of tasks, each represented by a Node, and manage their execution and dependencies.
        The package can be installed via :code:`pip install zntracck` or from source at https://github.com/zincware/zntrack .

    IPSuite
        IPSuite by :footcite:t:`zillsCollaborationMachineLearnedPotentials2024` is a software package for the development and application of machine-learned interatomic potentials (MLIPs). It provides functionalities for training and testing MLIPs, as well as for running simulations using these potentials.
        The package can be installed via :code:`pip install ipsuite` or from source at https://github.com/zincware/ipsuite .

    ZnDraw
        The :ref:`ZnDraw <zndraw>` package for visualisation and editing of atomistic structures :footcite:`elijosiusZeroShotMolecular2024`.
        The package can be installed via :code:`pip install zndraw` or from source at https://github.com/zincware/zndraw .

    main.py
        The :term:`ZnTrack` graph definition for the recipe is stored in this file.

    models.py
        The file that contains the models for testing.
        Each recipe will import the models from this file.
        It should follow the following format:

        .. code-block:: python

            from mlipx.abc import NodeWithCalculator

            MODELS: dict[str, NodeWithCalculator] = {
                ...
            }

    packmol
        Packmol is a software package used for building initial configurations for molecular dynamics or Monte Carlo simulations. It can generate a random collection of molecules using the specified density and composition. TODO add cite

    rdkit2ase
        A package for converting RDKit molecules to ASE atoms.
        The package can be installed via :code:`pip install rdkit2ase` or from source at https://github.com/zincware/rdkit2ase .

    Node
        A node is a class that represents a single step in the workflow.
        It should inherit from the :class:`zntrack.Node` class.
        The node should implement the :meth:`zntrack.Node.run` method.

    ASE
        The Atomic Simulation Environment (ASE). More information can be found at https://wiki.fysik.dtu.dk/ase/

    paraffin
        The paraffin package for the distributed evaluation of :term:`DVC` stages.
        The package can be installed via :code:`pip install paraffin` or from source at https://github.com/zincware/paraffin .


.. footbibliography::
