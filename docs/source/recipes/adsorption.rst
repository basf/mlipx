.. _neb:

Adsorption Energies
===================

This recipe calculates the adsorption energies of a molecule on a surface.
The following example creates a slab of ``Cu(111)`` and calculates the adsorption energy of ethanol ``(CCO)`` on the surface.

.. code-block:: console

   (.venv) $ mlipx recipes adsorption --models mace_mp,sevennet,orb_v2,mattersim --slab-config '{"crystal": "fcc111", "symbol": "Cu", "size": [3,4,4]}' --smiles CCO --repro
   (.venv) $ compare --glob "*RelaxAdsorptionConfigs"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*RelaxAdsorptionConfigs", "../../mlipx-hub/adsorption/cu_fcc111/")
   plots["adsorption_energies"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`RelaxAdsorptionConfigs`
* :term:`BuildASEslab`
* :term:`Smiles2Conformers`


.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/adsorption/cu_fcc111/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/adsorption/cu_fcc111/models.py
      :language: Python
