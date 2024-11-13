Phase Diagram
=============

:code:`mlipx` provides a command line interface to generate Phase Diagrams.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes phase-diagram

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"]
      end
      subgraph mg1["Model 1"]
         m1["PhaseDiagram"]
      end
      subgraph mg2["Model 2"]
         m2["PhaseDiagram"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["PhaseDiagram"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/formation-energy-comparison.json")
   figure.show()

   figure = pio.read_json("source/figures/mace_agnesiphase-diagram.json")
   figure.show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`PhaseDiagram`
