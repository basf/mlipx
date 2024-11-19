Phase Diagram
=============

:code:`mlipx` provides a command line interface to generate Phase Diagrams.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes phase-diagram

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


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import show

   show("formation-energy-comparison.json")
   show("mace_agnesiphase-diagram.json")


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`PhaseDiagram`
