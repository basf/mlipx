import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for material_id in ["mp-1143"]:
        data = mlipx.MPRester(search_kwargs={"material_ids": [material_id]})
        frames.append(mlipx.Rattle(data=data.frames, stdev=0.1))


for model_name, model in MODELS.items():
    for idx, data in enumerate(frames):
        with project.group(model_name, str(idx)):
            geom_opt = mlipx.StructureOptimization(
                data=data.frames, model=model, fmax=0.1
            )

project.build()
