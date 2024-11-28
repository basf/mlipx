Authors and Contributing
========================

.. note::

    Every contribution is welcome and you will be included in this ever growing list.

Authors
-------
The creation of ``mlipx`` began during Fabian Zills internship at BASF SE, where he worked under the guidance of Sandip De. The foundational concepts and designs were initially developed by Sandip, while the current version of the code is a product of contributions from various members of the BASF team. Fabian Zills integrated several of his previous projects and lead the technical development of the initial release of this code. The code has been released with the intention of fostering community involvement in future developments.  We acknowledge support from:

- Fabian Zills
- Sheena Agarwal
- Sandip De
- Shuang Han
- Srishti Gupta
- Tiago Joao Ferreira Goncalves


Contribution Guidelines
-----------------------

We welcome contributions to :code:`mlipx`!
With the inclusion of your contributions, we can make :code:`mlipx` better for everyone.

To ensure code quality and consistency, we use :code:`pre-commit` hooks.
To install the pre-commit hooks, run the following command:

.. code:: console

   (.venv) $ pre-commit install

All pre-commit hooks have to pass before a pull request can be merged.

For new recipes, we recommend adding an example to the ``\examples`` directory of this repository and updating the documentation accordingly.

**Plugins**

It is further possible, to add new recipes to ``mlipx`` by writing plugins.
We use the entry point ``mlipx.recipes`` to load new recipes.
You can find more information on entry points `here <https://setuptools.pypa.io/en/latest/userguide/entry_point.html>`_.

Given the following file ``yourpackage/recipes.py`` in your package:

.. code:: python

    from mlipx.recipes import app

    @app.command()
    def my_recipe():
        # Your recipe code here

you can add the following to your ``pyproject.toml``:

.. code:: toml

    [project.entry-points."mlipx.recipes"]
    yourpackage = "yourpackage.recipes"


and when your package is installed together with ``mlipx``, the recipe will be available in the CLI via ``mlipx recipes my_recipe``.
