Phase Diagram
=============

:code:`mlipx` provides a command line interface to generate Phase Diagrams.
You can run the following command to instantiate a test directory:

.. mdinclude:: ../../../mlipx-hub/phase_diagram/mp-30084/README.md


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*PhaseDiagram", "../../mlipx-hub/phase_diagram/mp-30084/")
   for name, plot in plots.items():
      if name.endswith("phase-diagram"):
         plot.show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PhaseDiagram`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/phase_diagram/mp-30084/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/phase_diagram/mp-30084/models.py
      :language: Python
