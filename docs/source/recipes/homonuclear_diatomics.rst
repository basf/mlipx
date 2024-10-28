Homonuclear Diatomics
===========================
Homonuclear diatomics give a per-element information on the performance of the :term:`mlip`.


.. code-block:: console

   (.venv) $ mlipx recipes homonuclear-diatomics

.. mermaid::
   :align: center

   graph TD

      subgraph mg1["Model 1"]
         m1["HomonuclearDiatomics"]
      end
      subgraph mg2["Model 2"]
         m2["HomonuclearDiatomics"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["HomonuclearDiatomics"]
      end

You can edit the elements in the :term:`graph.py` file to include the elements you want to test.
The models to evaluate are defined in the :term:`models.py` file.
We will use the following definition combining :code:`mlipx.GenericASECalculator` and a custom :code:`SevenCalc` calculator.

.. note::

   See :ref:`custom_nodes` for more information on how to use custom nodes.

   .. dropdown:: Content of :code:`src/__init__.py`

      .. code-block:: python

         import dataclasses
         from ase.calculators.calculator import Calculator


         @dataclasses.dataclass
         class SevenCalc:
            model: str

            def get_calculator(self, **kwargs) -> Calculator:
               from sevenn.sevennet_calculator import SevenNetCalculator
               sevennet= SevenNetCalculator(self.model, device='cpu')

               return sevennet

.. dropdown:: Content of :code:`models.py`

   .. code-block:: python

      import mlipx
      from src import SevenCalc


      mace_medium = mlipx.GenericASECalculator(
         module="mace.calculators",
         class_name="MACECalculator",
         device='auto',
         kwargs={
            "model_paths": "mace_models/y7uhwpje-medium.model",
         },
      )

      mace_agnesi = mlipx.GenericASECalculator(
         module="mace.calculators",
         class_name="MACECalculator",
         device='auto',
         kwargs={
            "model_paths": "mace_models/mace_mp_agnesi_medium.model",
         },
      )

      sevennet = SevenCalc(model='7net-0')

      MODELS = {
         "mace_medm": mace_medium,
         "mace_agne": mace_agnesi,
         "7net": sevennet,
      }



In the following we show the results for the :code:`Li-Li` bond for the three selected models.


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/Li-Li_bond.json")
   figure.show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`

A working example can be found at `here <https://gitlab.roqs.basf.net/qm-inorganics/mlip-tracking/mlip-evaluation-templates/-/tree/homonuclear-diatomics?ref_type=heads>`_.
