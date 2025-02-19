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

To install and develop :code:`mlipx` from source we recommend using :code:`https://docs.astral.sh/uv`.
More information and installation instructions can be found at https://docs.astral.sh/uv/getting-started/installation/ .

.. code:: console

   (.venv) $ git clone https://github.com/basf/mlipx
   (.venv) $ cd mlipx
   (.venv) $ uv sync
   (.venv) $ source .venv/bin/activate
