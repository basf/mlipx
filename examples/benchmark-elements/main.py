import zntrack
from models import MODELS

import mlipx

ELEMENTS = ["Cu"]
FILTERING_TYPE = "inclusive"

mptraj = zntrack.add(
    url="https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b/mp_traj_combined.xyz",
    path="mptraj.xyz",
)

project = zntrack.Project()

with project.group("mptraj"):
    raw_mptraj_data = mlipx.LoadDataFile(path=mptraj)
    mptraj_data = mlipx.FilterAtoms(
        data=raw_mptraj_data.frames, elements=ELEMENTS, filtering_type=FILTERING_TYPE
    )

for model_name, model in MODELS.items():
    with project.group(model_name, "diatomics"):
        neb = mlipx.HomonuclearDiatomics(
            elements=ELEMENTS,
            model=model,
            n_points=100,
            min_distance=0.5,
            max_distance=2.0,
        )

relaxed = []

for model_name, model in MODELS.items():
    with project.group(model_name, "struct_optim"):
        relaxed.append(
            mlipx.StructureOptimization(
                data=mptraj_data.frames, data_id=-1, model=model, fmax=0.1
            )
        )


mds = []

thermostat = mlipx.LangevinConfig(timestep=0.5, temperature=300, friction=0.05)
force_check = mlipx.MaximumForceObserver(f_max=100)
t_ramp = mlipx.TemperatureRampModifier(end_temperature=400, total_steps=100)

for (model_name, model), relaxed_structure in zip(MODELS.items(), relaxed):
    with project.group(model_name, "md"):
        mds.append(
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


for (model_name, model), md in zip(MODELS.items(), mds):
    with project.group(model_name):
        ev = mlipx.EnergyVolumeCurve(
            model=model,
            data=md.frames,
            data_id=-1,
            n_points=50,
            start=0.75,
            stop=2.0,
        )

for (model_name, model), md in zip(MODELS.items(), mds):
    with project.group(model_name, "struct_optim_2"):
        relaxed.append(
            mlipx.StructureOptimization(
                data=md.frames, data_id=-1, model=model, fmax=0.1
            )
        )


project.build()
