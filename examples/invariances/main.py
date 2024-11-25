import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for material_id in ["mp-1143"]:
        frames.append(mlipx.MPRester(search_kwargs={"material_ids": [material_id]}))


for model_name, model in MODELS.items():
    for idx, data in enumerate(frames):
        with project.group(model_name, str(idx)):
            rot = mlipx.RotationalInvariance(
                model=model,
                n_points=100,
                data=data.frames,
            )
            trans = mlipx.TranslationalInvariance(
                model=model,
                n_points=100,
                data=data.frames,
            )
            perm = mlipx.PermutationInvariance(
                model=model,
                n_points=100,
                data=data.frames,
            )

project.build()
