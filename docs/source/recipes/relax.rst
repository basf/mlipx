.. _relax:

Structure Relaxation
====================

This recipe is used to test the performance of different models in performing structure relaxation.


.. code-block:: console

   (.venv) $ mlipx recipes relax --models mace_mp,sevennet,orb_v2,chgnet,mattersim --material-ids=mp-1143 --repro
   (.venv) $ mlipx compare --glob "*StructureOptimization"

.. note::

   If you relax a non-periodic system and your model yields a stress tensor of :code:`[inf, inf, inf, inf, inf, inf]` you have to add the :code:`--convert-nan` flag to the :code:`mlipx compare` or :code:`zndraw` command to convert them to :code:`None`.

.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*StructureOptimization", "../../examples/relax/")
   plots["adjusted_energy_vs_steps"].show()

This recipe uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`StructureOptimization`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/relax/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/relax/models.py
      :language: Python
