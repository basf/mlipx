import dataclasses

from ase.calculators.calculator import Calculator

import mlipx

# Example MLIP
mace_medium = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="MACECalculator",
    device="cpu",
    kwargs={"model_paths": "../models/mace_medium.model", "dtype": "float64"},
)

mace_agnesi = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="MACECalculator",
    device="cpu",
    kwargs={"model_paths": "../models/mace_agnesi.model", "dtype": "float64"},
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
    name: "orb_v2"

    def get_calculator(self) -> Calculator:
        from orb_models.forcefield import pretrained
        from orb_models.forcefield.calculator import ORBCalculator

        method = getattr(pretrained, self.name)
        orbff = method(device="cpu")
        orb_calc = ORBCalculator(orbff, device="cpu")
        return orb_calc


orb_v2_mptraj = OrbCalc(name="orb_mptraj_only_v2")
orb_v2 = OrbCalc(name="orb_v2")
orb_d3_v2 = OrbCalc(name="orb_d3_v2")
orb_d3_sm_v2 = OrbCalc(name="orb_d3_sm_v2")
orb_d3_xs_v2 = OrbCalc(name="orb_d3_xs_v2")


# List all MLIPs to test in this dictionary
MODELS = {
    "mace_medium": mace_medium,
    "mace_agnesi": mace_agnesi,
    "7net": sevennet,
    "Orb_v2": orb_v2,
    "Orb_d3_v2": orb_d3_v2,
    "Orb_d3_sm_v2": orb_d3_sm_v2,
    "Orb_d3_xs_v2": orb_d3_xs_v2,
    "Orb_mptraj_v2": orb_v2_mptraj,
}

# OPTIONAL
# ========
# If you have custom property names you can use the UpdatedFramesCalc
# to set the energy, force and isolated_energies keys mlipx expects.
REFERENCE = mlipx.UpdateFramesCalc(
    results_mapping={"energy": "DFT_ENERGY", "forces": "DFT_FORCES"},
    info_mapping={mlipx.abc.ASEKeys.isolated_energies.value: "isol_ene"},
)
