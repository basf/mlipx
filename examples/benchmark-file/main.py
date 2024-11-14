import ase.io
import zntrack
from models import MODELS

import mlipx

DATAPATH = "../data/mp_data_mp-771359.extxyz"

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
        neb = mlipx.HomonuclearDiatomics(
            elements=ELEMENTS,
            model=model,
            n_points=100,
            min_distance=0.5,
            max_distance=2.0,
        )

relaxed = {x: [] for x in range(count)}

for model_name, model in MODELS.items():
    for idx in range(count):
        with project.group(model_name, "struct_optim", str(idx)):
            relaxed[idx].append(
                mlipx.StructureOptimization(
                    data=data.frames, data_id=idx, model=model, fmax=0.1
                )
            )


mds = {x: [] for x in range(count)}

thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)
force_check = mlipx.MaximumForceObserver(f_max=100)
t_ramp = mlipx.TemperatureRampModifier(end_temperature=400, total_steps=100)

for idx in range(count):
    for (model_name, model), relaxed_structure in zip(MODELS.items(), relaxed[idx]):
        with project.group(model_name, "md", str(idx)):
            mds[idx].append(
                mlipx.MolecularDynamics(
                    model=model,
                    thermostat=thermostat,
                    data=relaxed_structure.frames,
                    data_id=-1,
                    observers=[force_check],
                    modifiers=[t_ramp],
                    steps=100,
                )
            )

for idx in range(count):
    for (model_name, model), md in zip(MODELS.items(), mds[idx]):
        with project.group(model_name, "ev", str(idx)):
            ev = mlipx.EnergyVolumeCurve(
                model=model,
                data=md.frames,
                data_id=-1,
                n_points=50,
                start=0.75,
                stop=2.0,
            )
for idx in range(count):
    for (model_name, model), md in zip(MODELS.items(), mds[idx]):
        with project.group(model_name, "struct_optim_2", str(idx)):
            mlipx.StructureOptimization(
                data=md.frames, data_id=-1, model=model, fmax=0.1
            )


project.build()
