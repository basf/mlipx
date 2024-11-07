import mlipx

# Example MLIP
mace_mp0 = mlipx.GenericASECalculator(
    module="mace.calculators.mace_mp",
    class_name="mace_mp",
    device="auto",
    kwargs={"model": "medium"},
)

# List all MLIPs to test in this dictionary
MODELS = {"mace_mp0": mace_mp0}

# OPTIONAL
# ========
# If you have custom property names you can use the UpdatedFramesCalc
# to set the energy, force and isolated_energies keys mlipx expects.
REFERENCE = mlipx.UpdateFramesCalc(
    results_mapping={"energy": "DFT_ENERGY", "forces": "DFT_FORCES"},
    info_mapping={mlipx.abc.ASEKeys.isolated_energies.value: "isol_ene"},
)
