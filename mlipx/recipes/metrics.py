import zntrack
from models import MODELS

try:
    from models import REFERENCE
except ImportError:
    REFERENCE = None

import mlipx

DATAPATH = "{{ datapath }}"
ISOLATED_ATOM_ENERGIES = {{isolated_atom_energies}}  # noqa F821


project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)


with project.group("reference"):
    if REFERENCE is not None:
        data = mlipx.ApplyCalculator(data=data.frames, model=REFERENCE)
    ref_evaluation = mlipx.EvaluateCalculatorResults(data=data.frames)
    if ISOLATED_ATOM_ENERGIES:
        ref_isolated = mlipx.CalculateFormationEnergy(data=data.frames)

for model_name, model in MODELS.items():
    with project.group(model_name):
        updated_data = mlipx.ApplyCalculator(data=data.frames, model=model)
        evaluation = mlipx.EvaluateCalculatorResults(data=updated_data.frames)
        mlipx.CompareCalculatorResults(data=evaluation, reference=ref_evaluation)

        if ISOLATED_ATOM_ENERGIES:
            isolated = mlipx.CalculateFormationEnergy(
                data=updated_data.frames, model=model
            )
            mlipx.CompareFormationEnergy(data=isolated, reference=ref_isolated)

project.build()
