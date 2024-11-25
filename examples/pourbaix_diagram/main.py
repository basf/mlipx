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
            pd = mlipx.PourbaixDiagram(data=data.frames, model=model, pH=1.0, V=1.8)

project.build()
