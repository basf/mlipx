Energy and Force Evaluation
===========================

This recipe is used to test the performance of different models in predicting the energy and forces for a given dataset.

.. mdinclude:: ../../../mlipx-hub/metrics/DODH_adsorption/README.md

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


.. code-block:: console

   (.venv) $ mlipx compare --glob "*CompareCalculatorResults"

.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*CompareCalculatorResults", "../../mlipx-hub/metrics/DODH_adsorption/")
   # raise ValueError(plots.keys())
   plots["fmax_error"].show()
   plots["adjusted_energy_error_per_atom"].show()


This recipe uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`ApplyCalculator`
* :term:`EvaluateCalculatorResults`
* :term:`CalculateFormationEnergy`
* :term:`CompareCalculatorResults`
* :term:`CompareFormationEnergy`


.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../mlipx-hub/metrics/DODH_adsorption/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../mlipx-hub/metrics/DODH_adsorption/models.py
      :language: Python
