Models
======

For each recipe, the models to evaluate are defined in the :term:`models.py` file.
In most cases, you can use :code:`mlipx.GenericASECalculator` to access models.
However, in certain scenarios, you may need to provide a custom calculator.

Below, we demonstrate how to write a custom calculator node for :code:`SevenCalc`.
While this is an example, note that :code:`SevenCalc` could also be used with :code:`mlipx.GenericASECalculator`.

Defining Models
---------------

Here is the content of a typical :code:`models.py` file:

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

Custom Calculator Example
-------------------------

The :code:`SevenCalc` class, used in the example above, is defined in :code:`src/__init__.py` as follows:

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
            sevennet = SevenNetCalculator(self.model, device='cpu')

            return sevennet

For more details, refer to the :ref:`custom_nodes` section.

.. _serve-integration:

Serve Integration
-----------------

The dependencies of MLIPs can be incompatible, making it impossible to run multiple MLIPs in the same environment.
To address this, ``mlipx`` can circumvent this using ``uv`` (https://docs.astral.sh/uv/) in combination with ZeroMQ (https://zeromq.org/) to automatically serve models from different environments.

To make a model available for serving, you need to make it installable through an extra for ``mlipx``.
For this, you need to configure a new extra in the ``mlipx`` ``pyproject.toml`` using ``[tool.uv]
conflicts`` to specify dependencies that cannot be installed in the same environment.

Additionally, you need to include this extra in the model definition.

.. code-block:: python

   import mlipx

   ALL_MODELS["mace-mpa-0"] = mlipx.GenericASECalculator(
       module="mace.calculators",
       class_name="mace_mp",
       device="auto",
       extra=["mace"],  #  mlipx extras for this model
   )

**Using served models:**

.. code-block:: python

   # Environment variable (global control)
   import os
   os.environ["MLIPX_USE_SERVE"] = "true"

   # Or explicit per-model control
   calc = model.get_calculator(use_serve=True)

See :ref:`serve` for details on starting brokers, managing workers, and DVC integration.

.. _update-frames-calc:

Updating Dataset Keys
---------------------

In some cases, models may need to be defined to convert existing dataset keys into the format :code:`mlipx` expects.
For example, you may need to provide isolated atom energies or convert data where energies are stored as :code:`atoms.info['DFT_ENERGY']`
and forces as :code:`atoms.arrays['DFT_FORCES']`.

Here’s how to define a model for such a scenario:

.. code-block:: python

    import mlipx

    REFERENCE = mlipx.UpdateFramesCalc(
        results_mapping={"energy": "DFT_ENERGY", "forces": "DFT_FORCES"},
        info_mapping={mlipx.abc.ASEKeys.isolated_energies.value: "isol_ene"},
    )
