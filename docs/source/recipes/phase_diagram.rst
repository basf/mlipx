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

   plots = get_plots("*PhaseDiagram", "../../mlipx-hub/phase_diagram/mp-30084/")
   for plot in plots.values():
       plot.show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PhaseDiagram`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/phase_diagram/mp-30084/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/phase_diagram/mp-30084/models.py
      :language: Python
