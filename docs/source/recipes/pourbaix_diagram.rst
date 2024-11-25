Pourbaix Diagram
================

:code:`mlipx` provides a command line interface to generate Pourbaix diagrams.

.. note::

   The Pourbaix diagram requires the installation of ``pip install mpcontribs-client``.

.. code-block:: console

   (.venv) $ mlipx recipes pourbaix-diagram  --models mace_mp,sevennet,orb_v2,chgnet --material-ids=mp-1143 --repro
   (.venv) $ mlipx compare --glob "*PourbaixDiagram"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*PourbaixDiagram", "../examples/pourbaix_diagram/")
   plots["mace_mp_0-pourbaix-diagram"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PourbaixDiagram`
