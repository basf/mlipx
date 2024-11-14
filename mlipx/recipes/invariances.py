import zntrack
from models import MODELS

import mlipx

DATAPATH = "{{ datapath }}"

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
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
