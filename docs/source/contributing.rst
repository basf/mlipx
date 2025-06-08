Contributing
============

We want to make ``mlipx`` a truly comprehensive tool for evaluating :term:`MLIP` models. That means making it easy for you to extend! Whether you're adding new nodes, recipes, or integrating new :term:`MLIP` models, this guide will walk you through the process.

For any changes to ``mlipx``, we recommend installing the package from source. You can find detailed instructions in the :ref:`install-from-source` section.

New Nodes
---------

Nodes are the building blocks of ``mlipx`` workflows. They represent individual computational steps in your evaluation.

To create a new node:

1.  Subclass :class:`zntrack.Node`: Your new node must inherit from the :class:`zntrack.Node` class and specify all required inputs and outputs. For more information have a look at the `ZnTrack documentation <https://zntrack.readthedocs.io/en/latest>`_.
2.  Implement the ``run`` method: This method will contain the core logic of your node.

You can follow the :doc:`notebooks/structure_relaxation` for a practical example of writing a new node.

Once you've developed your node, here's how to integrate it:

1.  Create a New Branch:

    .. code-block:: console

        (.venv) $ cd mlipx
        (.venv) $ git checkout -b <new-branch-name>

2.  Add Dependencies (if any): If your node requires additional Python packages, use ``uv`` to add them:

    .. code-block:: console

        (.venv) $ uv add <dependency>

    .. note::
        For less common dependencies, consider adding them as an extra.

3.  Add Your Node File: Create or amend a file in the ``mlipx/nodes`` directory with your new node's implementation.
4.  Make it Importable: Import your new node into ``mlipx/__init__.pyi`` and add it to the ``__all__`` list. This makes your node directly importable by users (e.g., ``from mlipx import MyNewNode``).
5.  Commit and Pull Request: Finally, commit your changes and create a pull request on the ``mlipx`` GitHub repository.

.. tip::

    We encourage you to provide metadata about the training data used for your model.
    This enables ``mlipx`` to inform users whether models can be compared directly, or if differences in _ab initio_ settings make comparisons unreliable.

    To support this, ``mlipx`` offers a `JSON Schema <https://json-schema.org/>`_-based metadata format, defined at ``mlipx/spec/mlips-schema.json``.
    You can install schema support in VS Code using the CLI command: ``mlipx install-vscode-schema``.

    We recommend including an ``mlips.yaml`` file in your model package at ``<your_package>/spec/mlips.yaml``.
    ``mlipx`` will automatically attempt to load this file and use it to inform users about the training data behind your model during comparisons.

    .. dropdown:: Training data definitions for MLIPS included in ``mlipx``

        These predefined MLIP entries are described in :code:`mlipx/spec/mlips.yaml`.

        .. literalinclude:: ../../mlipx/spec/mlips.yaml
            :language: YAML

    We also provide built-in abstractions for several public datasets.

    .. dropdown:: Public datasets supported by ``mlipx``

        These datasets are defined in :code:`mlipx/spec/datasets.yaml`.

        .. literalinclude:: ../../mlipx/spec/datasets.yaml
            :language: YAML

New Recipes
-----------

Recipes are pre-defined workflows that combine multiple nodes to perform a specific evaluation task. They are designed as Jinja2 templates.

To add a new recipe:

1.  **Create a Jinja2 Template**: In the ``mlipx/recipes`` directory, create a new file with the ``.py.jinja2`` extension. Structure your recipe following the examples of existing recipes.
2.  **Extend the CLI**: Integrate your new recipe into the ``mlipx`` command-line interface by modifying the ``mlipx/recipes/main.py`` file. We use the `Typer <https://typer.tiangolo.com/>`_ library for our CLI, so you can refer to the existing recipes in ``main.py`` for guidance on how to add your new command.


New Models
----------

``mlipx`` provides a streamlined way to incorporate new :term:`MLIP` models for evaluation. All available models are managed in the ``mlipx/recipes/models.py.jinja2`` file.

Models Supported by :code:`mlipx.GenericASECalculator`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your model is compatible with the :code:`mlipx.GenericASECalculator` interface, you can add it directly:

.. code-block:: python

    ALL_MODELS["<model-id>"] = mlipx.GenericASECalculator(
        module="<your_module>", # The Python module where your calculator class is located
        class_name="<YourCalculatorClass>", # The name of your calculator class
        device="auto", # Set to "auto" if using PyTorch and your calculator supports a 'device' argument
        kwargs={} # Any additional keyword arguments to pass to your calculator's constructor
    )

Replace ``<model-id>``, ``<your_module>``, and ``<YourCalculatorClass>`` with your model's specific details.

Models Not Supported by :code:`mlipx.GenericASECalculator`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your model does not fit the :code:`mlipx.GenericASECalculator` interface, you'll need to create a custom node. This new node should implement the :class:`mlipx.abc.NodeWithCalculator` interface and be placed within the ``mlipx/recipes/models.py.jinja2`` file. This ensures ``mlipx`` can properly interact with your model for evaluations.
