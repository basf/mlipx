.. _md:

Molecular Dynamics
==================
This recipe is used to test the performance of different models in molecular dynamics simulations.

.. code-block:: console

   (.venv) $ mlipx recipes md --models mace_mp,sevennet,orb_v2,chgnet,mattersim --material-ids=mp-1143 --repro
   (.venv) $ mlipx compare --glob "*MolecularDynamics"



.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*MolecularDynamics", "../../examples/md/")
   plots["energy_vs_steps_adjusted"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

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
