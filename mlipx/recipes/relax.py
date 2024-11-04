import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

with project:
    # assume a fixed dataset for now
    propanol = mlipx.Smiles2Conformers(smiles="CC(C)O", num_confs=5)

for model_name, model in MODELS.items():
    with project.group(model_name):
        geom_opt = mlipx.StructureOptimization(
            data=propanol.frames, data_id=-1, model=model, fmax=0.05
        )

project.build()
