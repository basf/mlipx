import dataclasses

from ase.calculators.calculator import Calculator

import mlipx

mace_medium = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="MACECalculator",
    device="auto",
    kwargs={
        "model_paths": "../models/mace_medium.model",
    },
)

mace_agnesi = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="MACECalculator",
    device="auto",
    kwargs={
        "model_paths": "../models/mace_agnesi.model",
    },
)

sevennet = mlipx.GenericASECalculator(
    module="sevenn.sevennet_calculator",
    class_name="SevenNetCalculator",
    device="auto",
    kwargs={
        "model": "7net-0",
    },
)


@dataclasses.dataclass
class OrbCalc:
    name: str = "orb_v1"

    def get_calculator(self) -> Calculator:
        from orb_models.forcefield import pretrained
        from orb_models.forcefield.calculator import ORBCalculator

        method = getattr(pretrained, self.name)
        orbff = method(device="cuda")
        orb_calc = ORBCalculator(orbff, device="cuda")
        return orb_calc


# orb_v1 = OrbCalc(name='orb_v1')
# orb_d3_v1 = OrbCalc(name='orb_d3_v1')
# orb_v1_mptraj = OrbCalc(name='orb_v1_mptraj_only')
orb_v2 = OrbCalc(name="orb_v2")
orb_d3_v2 = OrbCalc(name="orb_d3_v2")

MODELS = {
    "mace_medm": mace_medium,
    "mace_agne": mace_agnesi,
    "7net": sevennet,
    #   "orb_v1": orb_v1,
    #   "orb_d3_v1": orb_d3_v1,
    #   "orb_v1_mptraj": orb_v1_mptraj,
    "orb_v2": orb_v2,
    "orb_d3_v2": orb_d3_v2,
}
