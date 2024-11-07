import zntrack
from models import MODELS

import mlipx

DATAPATH = "{{ datapath }}"


project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)


with project.group("reference"):
    # TODO: remove rereence model
    updated_data = mlipx.ApplyCalculator(data=data.frames)
    w_f_energy = mlipx.CalculateFormationEnergy(data=updated_data.frames)
    ref_evaluation = mlipx.EvaluateCalculatorResults(data=w_f_energy.frames)

for model_name, model in MODELS.items():
    with project.group(model_name):
        updated_data = mlipx.ApplyCalculator(data=data.frames, model=model)
        w_f_energy = mlipx.CalculateFormationEnergy(data=updated_data.frames)
        evaluation = mlipx.EvaluateCalculatorResults(data=w_f_energy.frames)
        mlipx.CompareCalculatorResults(data=evaluation, reference=ref_evaluation)

project.build()
