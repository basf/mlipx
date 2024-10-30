Glossary
========

.. glossary::

    MLIP
        Machine learned interatomic potential.

    GIT
        A distributed version control system.

    DVC
        Data version control.

    mlflow
        An open source platform for model parameter and metric tracking.

    ZnTrack
        The ZnTrack package by :footcite:t:`zillsZnTrackDataCode2024`.

    IPSuite
        The IPSuite package by :footcite:t:`zillsCollaborationMachineLearnedPotentials2024`.

    ZnDraw
        The ZnDraw package by :footcite:t:`elijosiusZeroShotMolecular2024`.

    graph.py
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
        A package for building initial boxes.

    rdkit2ase
        A package for converting RDKit molecules to ASE atoms.


.. footbibliography::
