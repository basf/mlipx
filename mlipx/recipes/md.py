import zntrack
from models import MODELS

import mlipx

DATAPATH = "{{ datapath }}"

project = zntrack.Project()

thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)
force_check = mlipx.MaximumForceObserver(f_max=100)
t_ramp = mlipx.TemperatureRampModifier(end_temperature=400, total_steps=100)


with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.MolecularDynamics(
            model=model,
            thermostat=thermostat,
            data=data.frames,
            observers=[force_check],
            modifiers=[t_ramp],
            steps=1000,
        )

project.build()
