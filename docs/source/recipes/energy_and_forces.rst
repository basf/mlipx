Energy and Force Evaluation
===========================
TBA

.. code-block:: console

   (.venv) $ mlipx recipes metrics

.. mermaid::
   :align: center

   graph TD

      data['Reference Data incl. DFT E/F']
      data --> CalculateFormationEnergy1
      data --> CalculateFormationEnergy2
      data --> CalculateFormationEnergy3
      data --> CalculateFormationEnergy4

         subgraph Reference
            CalculateFormationEnergy1 --> EvaluateCalculatorResults1
         end

         subgraph mg1["Model 1"]
         CalculateFormationEnergy2 --> EvaluateCalculatorResults2
         EvaluateCalculatorResults2 --> CompareCalculatorResults2
         EvaluateCalculatorResults1 --> CompareCalculatorResults2
         end
         subgraph mg2["Model 2"]
            CalculateFormationEnergy3 --> EvaluateCalculatorResults3
            EvaluateCalculatorResults3 --> CompareCalculatorResults3
            EvaluateCalculatorResults1 --> CompareCalculatorResults3
         end
         subgraph mgn["Model <i>N</i>"]
            CalculateFormationEnergy4 --> EvaluateCalculatorResults4
            EvaluateCalculatorResults4 --> CompareCalculatorResults4
            EvaluateCalculatorResults1 --> CompareCalculatorResults4
         end


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import show
   show("eform_per_atom.json")

.. jupyter-execute::
   :hide-code:

   show("fmax.json")

.. jupyter-execute::
   :hide-code:

   show("adjusted_eform_error_per_atom.json")

.. jupyter-execute::
   :hide-code:

   show("fmax_error.json")


.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/metrics/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/metrics/models.py
      :language: Python
