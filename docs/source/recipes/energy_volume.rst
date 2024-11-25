.. _ev:

Energy Volume Curves
====================
Compute the energy-volume curve for a given material using multiple models.

.. code-block:: console

   (.venv) $ mlipx recipes ev --models mace_mp,sevennet,orb_v2,chgnet --material-ids=mp-1143 --repro


.. mermaid::
   :align: center

   graph TD

      subgraph Initialization
         MPRester
      end

      MPRester --> mg1
      MPRester --> mg2
      MPRester --> mgn

      subgraph mg1["Model 1"]
         m1["EnergyVolumeCurve"]
      end
      subgraph mg2["Model 2"]
         m2["EnergyVolumeCurve"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["EnergyVolumeCurve"]
      end


.. code:: console

   (.venv) $ mlipx compare --glob "*EnergyVolumeCurve"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*EnergyVolumeCurve", "../examples/energy-volume/")
   plots["adjusted_energy-volume-curve"].show()

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/energy-volume/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/energy-volume/models.py
      :language: Python
