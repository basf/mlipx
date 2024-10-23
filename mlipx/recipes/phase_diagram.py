import zntrack
from models import MODELS

import mlipx

DATAPATH = ...

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        pd = mlipx.PhaseDiagram(data=data.frames, model=model)


project.build()
