.. _homonuclear_diatomics:

Homonuclear Diatomics
===========================
Homonuclear diatomics give a per-element information on the performance of the :term:`MLIP`.


.. mdinclude:: ../../../mlipx-hub/diatomics/LiCl/README.md

You can edit the elements in the :term:`main.py` file to include the elements you want to test.
In the following we show the results for the :code:`Li-Li` bond for the three selected models.

.. code-block:: console

   (.venv) $ mlipx compare --glob "*HomonuclearDiatomics"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*HomonuclearDiatomics", "../../mlipx-hub/diatomics/LiCl/")
   plots["Li-Li bond (adjusted)"].show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/diatomics/LiCl/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/diatomics/LiCl/models.py
      :language: Python
