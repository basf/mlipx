Phase Diagram
=============

:code:`mlipx` provides a command line interface to generate Phase Diagrams.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes phase-diagram  --models mace_mp,sevennet,orb_v2,chgnet --material-ids=mp-1143 --repro

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"]
      end
      subgraph mg1["Model 1"]
         m1["PhaseDiagram"]
      end
      subgraph mg2["Model 2"]
         m2["PhaseDiagram"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["PhaseDiagram"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn

.. code-block:: console

   (.venv) $ mlipx compare --glob "*PhaseDiagram"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*PhaseDiagram", "../examples/phase_diagram/")
   plots["phase-diagram-comparison"].show()
   plots["formation-energy-comparison"].show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`PhaseDiagram`
