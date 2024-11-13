Models
======
For each recipe, the models to evaluate are defined in the :term:`models.py` file.
Most of the time :code:`mlipx.GenericASECalculator` can be used to access models.
Sometimes, a custom calculator has to be provided.
In the following we will show how to write a custom calculator node for :code:`SevenCalc`.
This is just an example, as the :code:`SevenCalc` could also be used with :code:`mlipx.GenericASECalculator`.

.. dropdown:: Content of :code:`models.py`
   :open:

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

Where the :code:`SevenCalc` is defined in :code:`src/__init__.py` as follows:

.. dropdown:: Content of :code:`src/__init__.py`
   :open:

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

More information on can be found in the :ref:`custom_nodes` section.


Another scenario where a model needs to be defined is for converting existing dataset keys into the ones :code:`mlipx` expects.
This could be the case for providing isolated atom energies or energies saved as :code:`atoms.info['DFT_ENERGY']` or forces saved as :code:`atoms.arrays['DFT_FORCES']`.

.. code:: python

    import mlipx

    REFERENCE = mlipx.UpdateFramesCalc(
        results_mapping={"energy": "DFT_ENERGY", "forces": "DFT_FORCES"},
        info_mapping={mlipx.abc.ASEKeys.isolated_energies.value: "isol_ene"},
    )
