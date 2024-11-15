Invariances
===========
Check the rotational, translational and permutational invariance of an :term:`mlip`.


.. code-block:: console

   (.venv) $ mlipx recipes invariances


This recipe uses:

* :term:`RotationalInvariance`
* :term:`StructureOptimization`
* :term:`PermutationInvariance`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/invariances/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/invariances/models.py
      :language: Python
