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

MODELS = {
    "mace_medm": mace_medium,
    "mace_agne": mace_agnesi,
    "7net": sevennet,
}
