Phase Diagram
=============

:code:`mlipx` provides a command line interface to generate Phase Diagrams.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes phase-diagram  --models mace_mp,sevennet,orb_v2,chgnet,mattersim --material-ids=mp-30084 --repro
   (.venv) $ mlipx compare --glob "*PhaseDiagram"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*PhaseDiagram", "../../examples/phase_diagram/")
   plots["mace_mp_0-phase-diagram"].show()
   plots["orb_v2_0-phase-diagram"].show()
   plots["sevennet_0-phase-diagram"].show()
   plots["chgnet_0-phase-diagram"].show()
   plots["mattersim_0-phase-diagram"].show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PhaseDiagram`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/phase_diagram/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/phase_diagram/models.py
      :language: Python
