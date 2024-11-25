Installation
============

From PyPI
---------

To use :code:`mlipx`, first install it using pip:

.. code-block:: console

   (.venv) $ pip install mlipx

.. note::

   The :code:`mlipx` package installation does not contain any :term:`MLIP` packages.
   Due to different dependencies, it is highly recommended to install your preferred :term:`MLIP` package individually into the same environment.

.. note::

   If you encounter en error like :code:`Permission denied '/var/cache/dvc'` you might want to reinstall :code:`pip install platformdirs==3.11.0` or :code:`pip install platformdirs==3.10.0` as discussed at https://github.com/iterative/dvc/issues/9184

From Source
-----------

To install and develop :code:`mlipx` from source we recommend using :code:`poetry`.
More information and installation instructions can be found at https://python-poetry.org .

.. code:: console

   (.venv) $ git clone https://github.com/basf/mlipx
   (.venv) $ cd mlipx
   (.venv) $ poetry install

.. note::

   You can also use :code:`pip install -e .` for a editable installation.
   This does not ensure that all dependencies are handled correctly and for adding new requirements it is mandatory to update the :code:`poetry.lock` file.

Contributing
------------
We welcome contributions to :code:`mlipx`!
With the inclusion of your contributions, we can make :code:`mlipx` better for everyone.

To ensure code quality and consistency, we use :code:`pre-commit` hooks.
To install the pre-commit hooks, run the following command:

.. code:: console

   (.venv) $ pre-commit install

All pre-commit hooks have to pass before a pull request can be merged.
