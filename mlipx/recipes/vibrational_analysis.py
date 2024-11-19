import zntrack
from models import MODELS

import mlipx

DATAPATH = ...

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        phon = mlipx.VibrationalAnalysis(
            data=data.frames,
            model=model,
            temperature=298.15,
            displacement=0.015,
            nfree=4,
            lower_freq_threshold=12,
        )


project.build()
