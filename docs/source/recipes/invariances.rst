Invariances
===========
Check the rotational, translational and permutational invariance of an :term:`mlip`.


.. mdinclude:: ../../../mlipx-hub/invariances/mp-1143/README.md


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*TranslationalInvariance", "../../mlipx-hub/invariances/mp-1143/")
   plots["energy_vs_steps_adjusted"].show()

   plots = get_plots("*RotationalInvariance", ".")
   plots["energy_vs_steps_adjusted"].show()

   plots = get_plots("*PermutationInvariance", ".")
   plots["energy_vs_steps_adjusted"].show()


This recipe uses:

* :term:`RotationalInvariance`
* :term:`StructureOptimization`
* :term:`PermutationInvariance`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/invariances/mp-1143/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/invariances/mp-1143/models.py
      :language: Python
