.. _homonuclear_diatomics:

Homonuclear Diatomics
===========================
Homonuclear diatomics give a per-element information on the performance of the :term:`MLIP`.


.. code-block:: console

   (.venv) $ mlipx recipes homonuclear-diatomics --models mace_mp,sevennet,orb_v2,mattersim --smiles="[Li+].[Cl-]" --repro


You can edit the elements in the :term:`main.py` file to include the elements you want to test.
In the following we show the results for the :code:`Li-Li` bond for the three selected models.

.. code-block:: console

   (.venv) $ mlipx compare --glob "*HomonuclearDiatomics"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*HomonuclearDiatomics", "../../mlipx-hub/diatomics/")
   plots["Li-Li bond (adjusted)"].show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/diatomics/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/diatomics/models.py
      :language: Python
