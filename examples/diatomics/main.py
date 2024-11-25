import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for smiles in ["[Li+].[Cl-]"]:
        frames.append(mlipx.Smiles2Conformers(smiles=smiles, num_confs=1).frames)


for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.HomonuclearDiatomics(
            elements=[],
            data=sum(frames, []),
            model=model,
            n_points=100,
            min_distance=0.5,
            max_distance=2.0,
        )

project.build()
