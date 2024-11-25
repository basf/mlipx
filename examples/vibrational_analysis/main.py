import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for smiles in ["CO", "CCO", "CCCO", "CCCCO"]:
        frames.append(mlipx.Smiles2Conformers(smiles=smiles, num_confs=1))


for model_name, model in MODELS.items():
    with project.group(model_name):
        phon = mlipx.VibrationalAnalysis(
            data=sum([x.frames for x in frames], []),
            model=model,
            temperature=298.15,
            displacement=0.015,
            nfree=4,
            lower_freq_threshold=12,
            system="molecule",
        )


project.build()
