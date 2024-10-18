import ase
import ase.optimize as opt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import zntrack

from mlipx.abc import ComparisonResults, NodeWithCalculator, Optimizer


class StructureOptimization(zntrack.Node):
    """Structure optimization Node.

    Relax the geometry for each `ase.Atoms` provided.

    Attributes
    ----------
    data : list[ase.Atoms]
        Atoms to relax.
    optimizer : Optimizer
        Optimizer to use.
    model : NodeWithCalculator
        Model to use.
    fmax : float
        Maximum force to reach before stopping.
    steps : int
        Maximum number of steps for each optimization.
    plots : pd.DataFrame
        Resulting energy and fmax for each step.
    trajectory_path : str
        Output directory for the optimization trajectories.

    """

    data: list[ase.Atoms] = zntrack.deps()
    optimizer: Optimizer = zntrack.params(Optimizer.LBFGS.value)
    model: NodeWithCalculator = zntrack.deps()
    fmax: float = zntrack.params(0.05)
    steps: int = zntrack.params(100_000_000)
    plots: pd.DataFrame = zntrack.plots(y=["energy", "fmax"], x="step")

    trajectory_path: str = zntrack.outs_path(zntrack.nwd / "trajectories")

    def run(self):
        optimizer = getattr(opt, self.optimizer)
        calc = self.model.get_calculator()
        self.trajectory_path.mkdir(parents=True, exist_ok=True)

        energies = []
        fmax = []

        for idx, atoms in enumerate(self.data):

            def metrics_callback():
                energies.append(atoms.get_potential_energy())
                fmax.append(np.linalg.norm(atoms.get_forces(), axis=-1).max())

            atoms.calc = calc
            trajectory_path = self.trajectory_path / f"trajectory_{idx}.traj"
            dyn = optimizer(
                atoms,
                trajectory=trajectory_path.as_posix(),
            )
            dyn.attach(metrics_callback)
            dyn.run(fmax=self.fmax, steps=self.steps)

        self.plots = pd.DataFrame({"energy": energies, "fmax": fmax})
        self.plots.index.name = "step"

    @property
    def trajectories(self) -> list[list[ase.Atoms]]:
        frames_list = []
        trajectories = list(
            self.state.fs.glob((self.trajectory_path / "trajectory_*.traj").as_posix())
        )
        for trajectory in trajectories:
            with self.state.fs.open(trajectory, "rb") as f:
                frames_list.append(list(ase.io.iread(f, format="traj")))
        return frames_list

    @property
    def frames(self) -> list[ase.Atoms]:
        return sum(self.trajectories, [])

    @property
    def figures(self) -> dict[str, go.Figure]:
        figure = go.Figure()
        offset = 0
        for idx, trajectory in enumerate(self.trajectories):
            energies = [atoms.get_potential_energy() for atoms in trajectory]
            figure.add_trace(
                go.Scatter(
                    x=list(range(len(energies))),
                    y=energies,
                    mode="lines+markers",
                    name=f"trajectory_{idx}",
                    customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
                )
            )
            offset += len(energies)
        figure.update_layout(
            title="Energy vs. Steps",
            xaxis_title="Steps",
            yaxis_title="Energy",
        )
        return {"energy_vs_steps": figure}

    @staticmethod
    def compare(*nodes: "StructureOptimization") -> ComparisonResults:
        frames = sum([node.frames for node in nodes], [])
        offset = 0
        fig = go.Figure()
        for idx, node in enumerate(nodes):
            energies = [atoms.get_potential_energy() for atoms in node.frames]
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(energies))),
                    y=energies,
                    mode="lines+markers",
                    name=node.name,
                    customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
                )
            )
            offset += len(energies)
        return ComparisonResults(
            frames=frames,
            figures={"energy_vs_steps": fig},
        )
