Nudged Elastic Band
===================

:code:`mlipx` provides a command line interface to interpolate and create a NEB path from inital-final or initial-ts-final images and run NEB on the interpolated images.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes neb

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"] --> setup2["NEBinterpolate"]

      end
      subgraph mg1["Model 1"]
         m1["NEBs"]
      end
      subgraph mg2["Model 2"]
         m2["NEBs"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["NEBs"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn


.. code-block:: console

   (.venv) $ zntrack list # show available Nodes
   (.venv) $ mlipx compare --glob '*NEBs'


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/neb.json")
   figure.show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`NEBinterpolate`
* :term:`NEBs`


.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/neb/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/neb/models.py
      :language: Python
