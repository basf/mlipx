import zntrack
from models import MODELS

import mlipx

DATAPATH = "../data/neb_end_p.xyz"

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)
    trajectory = mlipx.NEBinterpolate(data=data.frames, n_images=5, mic=True)

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.NEBs(
            data=trajectory.frames,
            model=model,
            relax=True,
            fmax=0.05,
        )

project.build()
