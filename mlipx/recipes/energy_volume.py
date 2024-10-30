import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

with project.group("initialize"):
    confs = mlipx.Smiles2Conformers(smiles="CCO", num_confs=10)
    data = mlipx.BuildBox(data=[confs.frames], counts=[10], density=789)

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.EnergyVolumeCurve(
            model=model,
            data=data.frames,
            n_points=50,
            start=0.75,
            stop=2.0,
        )

project.build()
