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
            neb = mlipx.EnergyVolumeCurve(
                model=model,
                data=data.frames,
                n_points=50,
                start=0.8,
                stop=2.0,
            )

project.build()
