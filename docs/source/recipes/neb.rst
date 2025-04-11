.. _neb:

Nudged Elastic Band
===================

:code:`mlipx` provides a command line interface to interpolate and create a NEB path from inital-final or initial-ts-final images and run NEB on the interpolated images.
You can run the following command to instantiate a test directory:

.. mdinclude:: ../../../mlipx-hub/neb/ex01/README.md


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*NEBs", "../../mlipx-hub/neb/ex01/")
   plots["adjusted_energy_vs_neb_image"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`NEBinterpolate`
* :term:`NEBs`


.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/neb/ex01/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/neb/ex01/models.py
      :language: Python
