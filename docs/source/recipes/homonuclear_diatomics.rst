Homonuclear Diatomics
===========================
Homonuclear diatomics give a per-element information on the performance of the :term:`mlip`.


.. code-block:: console

   (.venv) $ mlipx recipes homonuclear-diatomics

.. mermaid::
   :align: center

   graph TD

      subgraph mg1["Model 1"]
         m1["HomonuclearDiatomics"]
      end
      subgraph mg2["Model 2"]
         m2["HomonuclearDiatomics"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["HomonuclearDiatomics"]
      end

You can edit the elements in the :term:`main.py` file to include the elements you want to test.



In the following we show the results for the :code:`Li-Li` bond for the three selected models.

.. code-block:: console

   (.venv) $ mlipx compare --glob "*HomonuclearDiatomics"


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/Li-Li_bond.json")
   figure.show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/diatomics/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/diatomics/models.py
      :language: Python
