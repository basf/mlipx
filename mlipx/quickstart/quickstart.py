import zntrack

import mlipx

project = mlipx.Project()

mptraj = zntrack.add(
    url="https://github.com/zincware/ips-mace/releases/download/v0.1.0/mptraj_slice.xyz",
    path="mptraj_slice.xyz",
)

mace_mp = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={
        "model": "medium",
    },
)

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=mptraj)

with project.group("reference"):
    ref_evaluation = mlipx.EvaluateCalculatorResults(data=data.frames)

with project.group("mace-mp", "metrics"):
    updated_data = mlipx.ApplyCalculator(data=data.frames, model=mace_mp)
    evaluation = mlipx.EvaluateCalculatorResults(data=updated_data.frames)
    mlipx.CompareCalculatorResults(data=evaluation, reference=ref_evaluation)


with project.group("mace-mp", "EV"):
    for data_id in [1, 2, 3]:
        mlipx.EnergyVolumeCurve(
            model=mace_mp,
            data=data.frames,
            data_id=data_id,
            n_points=50,
            start=0.75,
            stop=2.0,
        )

with project:
    rattle = mlipx.Rattle(data=data.frames, stdev=0.1)

with project.group("mace-mp", "geomopt"):
    for data_id in [1, 2, 3]:
        _ = mlipx.StructureOptimization(
            data=rattle.frames, data_id=data_id, model=mace_mp, fmax=0.1
        )

with project.group("mace-mp", "diatomics"):
    mlipx.HomonuclearDiatomics(
        model=mace_mp,
        elements=["C", "O", "N"],
        n_points=100,
        min_distance=0.5,
        max_distance=2.0,
    )


project.repro()
