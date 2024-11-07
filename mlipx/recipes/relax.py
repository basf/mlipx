import zntrack
from models import MODELS

import mlipx

DATAPATH = "{{ datapath }}"

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        geom_opt = mlipx.StructureOptimization(data=data.frames, model=model, fmax=0.1)

project.build()
