import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

with project.group("initialize"):
    confs = mlipx.Smiles2Conformers(smiles="CCO", num_confs=10)
    data = mlipx.BuildBox(data=[confs.frames], counts=[10], density=789)

thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.MolecularDynamics(
            model=model, data=data.frames, data_id=-1, thermostat=thermostat, steps=100
        )

project.build()
