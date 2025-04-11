Pourbaix Diagram
================

:code:`mlipx` provides a command line interface to generate Pourbaix diagrams.


.. mdinclude:: ../../../mlipx-hub/pourbaix_diagram/mp-1143/README.md


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*PourbaixDiagram", "../../mlipx-hub/pourbaix_diagram/mp-1143/")
   for plot in plots.values():
      plot.show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PourbaixDiagram`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/pourbaix_diagram/mp-1143/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/pourbaix_diagram/mp-1143/models.py
      :language: Python
