import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.Smiles2Conformers(smiles="C12C3C1C4C2C34", num_confs=100)

for model_name, model in MODELS.items():
    with project.group(model_name):
        geom_opt = mlipx.StructureOptimization(data=data.frames, model=model, fmax=0.1)

project.build()
