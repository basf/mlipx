import ase.io
import zntrack
from models import MODELS

import mlipx

DATAPATH = "{{ datapath }}"

count = 0
ELEMENTS = set()
for atoms in ase.io.iread(DATAPATH):
    count += 1
    for symbol in atoms.symbols:
        ELEMENTS.add(symbol)
ELEMENTS = list(ELEMENTS)

project = zntrack.Project()

with project.group("mptraj"):
    data = mlipx.LoadDataFile(path=DATAPATH)


for model_name, model in MODELS.items():
    with project.group(model_name, "diatomics"):
        _ = mlipx.HomonuclearDiatomics(
            elements=ELEMENTS,
            model=model,
            n_points=100,
            min_distance=0.5,
            max_distance=2.0,
        )

# Energy-Volume Curve
for model_name, model in MODELS.items():
    for idx in range(count):
        with project.group(model_name, "ev", str(idx)):
            _ = mlipx.EnergyVolumeCurve(
                model=model,
                data=data.frames,
                data_id=idx,
                n_points=50,
                start=0.75,
                stop=2.0,
            )


# Molecular Dynamics
thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)
force_check = mlipx.MaximumForceObserver(f_max=100)
t_ramp = mlipx.TemperatureRampModifier(end_temperature=400, total_steps=100)

for model_name, model in MODELS.items():
    for idx in range(count):
        with project.group(model_name, "md", str(idx)):
            _ = mlipx.MolecularDynamics(
                model=model,
                thermostat=thermostat,
                data=data.frames,
                data_id=idx,
                observers=[force_check],
                modifiers=[t_ramp],
                steps=100,
            )

# Structure Optimization
with project.group("rattle"):
    rattle = mlipx.Rattle(data=data.frames, stdev=0.01)

for model_name, model in MODELS.items():
    for idx in range(count):
        with project.group(model_name, "struct_optim", str(idx)):
            _ = mlipx.StructureOptimization(
                data=rattle.frames, data_id=idx, model=model, fmax=0.1
            )

project.build()
