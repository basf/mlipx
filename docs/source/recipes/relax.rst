Structure Relaxation
====================

:code:`mlipx` provides a command line interface to perform structural relaxations.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes relax

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["Smiles2Conformers"]
      end
      subgraph mg1["Model 1"]
         m1["StructureOptimization"]
      end
      subgraph mg2["Model 2"]
         m2["StructureOptimization"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["StructureOptimization"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn

With this recipe we can compare the structure relaxation for three different models on the same starting configuration.

.. code:: console

   mlipx compare --glob '*StructureOptimization'

.. note::

   If you relax a non-periodic system and your model yields a stress tensor of :code:`[inf, inf, inf, inf, inf, inf]` you have to add the :code:`--convert-nan` flag to the :code:`mlipx` or :code:`zndraw` command to convert them to :code:`None`.

.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/geomopt.json")
   figure.show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`Smiles2Conformers`
* :term:`StructureOptimization`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/relax/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/relax/models.py
      :language: Python
