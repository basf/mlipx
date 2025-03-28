.. _ev:

Energy Volume Curves
====================
Compute the energy-volume curve for a given material using multiple models.

.. code-block:: console

   (.venv) $ mlipx recipes ev --models mace_mp,sevennet,orb_v2,chgnet,mattersim --material-ids=mp-1143 --repro
   (.venv) $ mlipx compare --glob "*EnergyVolumeCurve"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*EnergyVolumeCurve", "../../mlipx-hub/mp-1143/energy-volume/")
   plots["adjusted_energy-volume-curve"].show()


This recipe uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`EnergyVolumeCurve`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/energy-volume/mp-1143/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/energy-volume/mp-1143/models.py
      :language: Python
