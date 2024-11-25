.. _md:

Molecular Dynamics
==================
This recipe is used to test the performance of different models in molecular dynamics simulations.

.. code-block:: console

   (.venv) $ mlipx recipes md --models mace_mp,sevennet,orb_v2,chgnet --material-ids=mp-1143 --repro

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"]
         setup2["LangevinConfig"]
         setup3["MaximumForceObserver"]
         setup4["TemperatureRampModifier"]
      end
      subgraph mg1["Model 1"]
         m1["MolecularDynamics"]
      end
      subgraph mg2["Model 2"]
         m2["MolecularDynamics"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["MolecularDynamics"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn


.. code-block:: console

   (.venv) $ mlipx compare --glob "*MolecularDynamics"



.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*MolecularDynamics", "../examples/md/")
   plots["energy_vs_steps_adjusted"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`LangevinConfig`
* :term:`MaximumForceObserver`
* :term:`TemperatureRampModifier`
* :term:`MolecularDynamics`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/md/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/md/models.py
      :language: Python
