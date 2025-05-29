Contributing
============

We aim to make ``mlipx`` easily extensible to provide a comprehensive set of recipes and nodes for the evaluation of :term:`MLIP` models.

For all changes to ``mlipx``, we recommend installing the package from source as described in the :ref:`install-from-source` section.

New Nodes
---------
Create a new node by subclassing the :class:`zntrack.Node` class and implementing the `run` method. The node should follow the naming conventions and structure of existing nodes in the ``mlipx`` package.
As an example you can follow along this notebook :doc:`notebooks/structure_relaxation`.

To add the node to ``mlipx``, follow create a new branch.

.. code-block:: console

    (.venv) $ cd mlipx
    (.venv) $ git checkout -b <new-branch-name>

If you need any additional dependencies, add them using the `uv`.

.. code-block:: console

    (.venv) $ uv add <dependency>

.. note::

    If you require non-common dependencies, consider adding them as an extra.

Now amend or create a new file in the ``mlipx/nodes`` directory with your new node implementation.
Import your new node into `mlipx/__init__.pyi` and include it in the `__all__` list to make it available for import.

Finally, commit your changes and create a pull request.

New Recipes
-----------

Recipes are defined as a jinja2 template in the `mlipx/recipes` directory.
Create a new file with the `.py.jinja2` extension and follow the structure of existing recipes.
Additionally, extend the ``mlipx`` CLI by including your new recipe in the `mlipx/recipes/main.py` file.
We utilize the typer (TODO: add link) library for the CLI, so you can follow the existing recipes as examples.

New Models
----------

``mlipx`` manages all available models in the `mlipx/recipes/models.py.jinja2` file.
If your model is supported by the :class:`mlipx.GenericASECalculator`, you can add it directly as follows:

.. code-block:: python

    ALL_MODELS["<model-id>"] = mlipx.GenericASECalculator(
        module="<your_module>",
        class_name="<YourCalculatorClass>",
        device="auto", # if using torch and the model calculator has a device argument
        kwargs={} # additional keyword arguments for the calculator
    )

If your model is not supported by the :class:`mlipx.GenericASECalculator`, you can create a new node that implements the :class:`mlipx.abc.NodeWithCalculator` interface inside the `mlipx/recipes/models.py.jinja2` file.
