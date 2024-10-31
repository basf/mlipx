Vibrational Analysis
====================

:code:`mlipx` provides a command line interface to vibrational analysis.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes vibrational-analysis

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"]
      end
      subgraph mg1["Model 1"]
         m1["VibrationalAnalysis"]
      end
      subgraph mg2["Model 2"]
         m2["VibrationalAnalysis"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["VibrationalAnalysis"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`VibrationalAnalysis`
