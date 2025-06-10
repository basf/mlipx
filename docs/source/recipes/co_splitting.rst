CO Splitting
============

:code:`mlipx` provides a recipe to perform a CO splitting analysis on a provided interface.

.. mdinclude:: ../../../mlipx-hub/co-splitting/mp-30/README.md


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*COSplitting", "../../mlipx-hub/co-splitting/mp-30/")
   plots["Reaction-Comparison"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`COSplitting`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/co-splitting/mp-30/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/co-splitting/mp-30/models.py
      :language: Python
