.. _md:

Molecular Dynamics
==================
This recipe is used to test the performance of different models in molecular dynamics simulations.

.. mdinclude:: ../../../mlipx-hub/md/mp-1143/README.md



.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*MolecularDynamics", "../../mlipx-hub/md/mp-1143/")
   plots["energy_vs_steps_adjusted"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LangevinConfig`
* :term:`MaximumForceObserver`
* :term:`TemperatureRampModifier`
* :term:`MolecularDynamics`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/md/mp-1143/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/md/mp-1143/models.py
      :language: Python
