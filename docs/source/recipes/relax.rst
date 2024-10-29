Structure Relaxation
====================

:code:`mlipx` provides a command line interface to perform structural relaxations.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes relax

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["Smiles2Conformers"]
      end
      subgraph mg1["Model 1"]
         m1["StructureOptimization"]
      end
      subgraph mg2["Model 2"]
         m2["StructureOptimization"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["StructureOptimization"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`Smiles2Conformers`
* :term:`StructureOptimization`
