import zntrack
from models import MODELS

import mlipx

DATAPATH = "../data/mp_data_mp-1143_conventional_standard.cif"

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.EnergyVolumeCurve(
            model=model,
            data=data.frames,
            n_points=50,
            start=0.75,
            stop=2.0,
        )

project.build()
