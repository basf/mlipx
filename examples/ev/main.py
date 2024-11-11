import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

mptraj = zntrack.add(
    url="https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b/mp_traj_combined.xyz",
    path="mptraj.xyz",
)

with project:
    data = mlipx.LoadDataFile(path=mptraj)
    filtered = mlipx.FilterAtoms(
        data=data.frames, elements=["B", "F"], filtering_type="exclusive"
    )


for data_id in range(5):
    for model_name, model in MODELS.items():
        with project.group(f"frame_{data_id}", model_name):
            neb = mlipx.EnergyVolumeCurve(
                model=model,
                data=filtered.frames,
                data_id=data_id,
                n_points=50,
                start=0.75,
                stop=2.0,
            )

project.build()
