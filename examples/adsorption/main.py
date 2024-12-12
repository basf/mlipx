import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

slabs = []

with project.group("initialize"):
    slabs.append(
        mlipx.BuildASEslab(
            **{"crystal": "fcc111", "symbol": "Cu", "size": [3, 4, 4]}
        ).frames
    )

adsorbates = []

with project.group("initialize"):
    for smiles in ["CCO"]:
        adsorbates.append(mlipx.Smiles2Conformers(smiles=smiles, num_confs=1).frames)


for model_name, model in MODELS.items():
    for idx, slab in enumerate(slabs):
        for jdx, adsorbate in enumerate(adsorbates):
            with project.group(model_name, str(idx)):
                _ = mlipx.RelaxAdsorptionConfigs(
                    slabs=slab,
                    adsorbates=adsorbate,
                    model=model,
                )

project.build()
