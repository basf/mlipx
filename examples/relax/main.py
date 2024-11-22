import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for smiles in ["CCO", "C1=CC2=C(C=C1O)C(=CN2)CCN"]:
        frames.append(mlipx.Smiles2Conformers(smiles=smiles, num_confs=1))


for model_name, model in MODELS.items():
    for idx, data in enumerate(frames):
        with project.group(model_name, str(idx)):
            geom_opt = mlipx.StructureOptimization(
                data=data.frames, model=model, fmax=0.1
            )

project.build()
