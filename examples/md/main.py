import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

frames = []

with project.group("initialize"):
    for material_id in ["mp-1143"]:
        frames.append(mlipx.MPRester(search_kwargs={"material_ids": [material_id]}))


thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)
force_check = mlipx.MaximumForceObserver(f_max=100)
t_ramp = mlipx.TemperatureRampModifier(end_temperature=400, total_steps=100)


for model_name, model in MODELS.items():
    for idx, data in enumerate(frames):
        with project.group(model_name, str(idx)):
            neb = mlipx.MolecularDynamics(
                model=model,
                thermostat=thermostat,
                data=data.frames,
                observers=[force_check],
                modifiers=[t_ramp],
                steps=1000,
            )

project.build()
