import pathlib

import ase.io
import ase.optimize as opt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import zntrack

from mlipx.abc import ComparisonResults, NodeWithCalculator, Optimizer


class StructureOptimization(zntrack.Node):
    """Structure optimization Node.

    Relax the geometry for the selected `ase.Atoms`.

    Parameters
    ----------
    data : list[ase.Atoms]
        Atoms to relax.
    data_id: int, default=-1
        The index of the ase.Atoms in `data` to optimize.
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
    data_id: int = zntrack.params(-1)
    optimizer: Optimizer = zntrack.params(Optimizer.LBFGS.value)
    model: NodeWithCalculator = zntrack.deps()
    fmax: float = zntrack.params(0.05)
    steps: int = zntrack.params(100_000_000)
    plots: pd.DataFrame = zntrack.plots(y=["energy", "fmax"], x="step")

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.traj")

    def run(self):
        optimizer = getattr(opt, self.optimizer)
        calc = self.model.get_calculator()

        atoms = self.data[self.data_id]
        self.frames_path.parent.mkdir(exist_ok=True)

        energies = []
        fmax = []

        def metrics_callback():
            energies.append(atoms.get_potential_energy())
            fmax.append(np.linalg.norm(atoms.get_forces(), axis=-1).max())

        atoms.calc = calc
        dyn = optimizer(
            atoms,
            trajectory=self.frames_path.as_posix(),
        )
        dyn.attach(metrics_callback)
        dyn.run(fmax=self.fmax, steps=self.steps)

        self.plots = pd.DataFrame({"energy": energies, "fmax": fmax})
        self.plots.index.name = "step"

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "rb") as f:
            return list(ase.io.iread(f, format="traj"))

    @property
    def figures(self) -> dict[str, go.Figure]:
        figure = go.Figure()

        energies = [atoms.get_potential_energy() for atoms in self.frames]
        figure.add_trace(
            go.Scatter(
                x=list(range(len(energies))),
                y=energies,
                mode="lines+markers",
                customdata=np.stack([np.arange(len(energies))], axis=1),
            )
        )

        figure.update_layout(
            title="Energy vs. Steps",
            xaxis_title="Step",
            yaxis_title="Energy",
        )

        ffigure = go.Figure()
        ffigure.add_trace(
            go.Scatter(
                x=self.plots.index,
                y=self.plots["fmax"],
                mode="lines+markers",
                customdata=np.stack([np.arange(len(energies))], axis=1),
            )
        )

        ffigure.update_layout(
            title="Fmax vs. Steps",
            xaxis_title="Step",
            yaxis_title="Maximum force",
        )
        return {"energy_vs_steps": figure, "fmax_vs_steps": ffigure}

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
                    name=node.name.replace(f"_{node.__class__.__name__}", ""),
                    customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
                )
            )
            offset += len(energies)

        fig.update_layout(
            title="Energy vs. Steps",
            xaxis_title="Step",
            yaxis_title="Energy",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
            zeroline=False,
        )

        # now adjusted

        offset = 0
        fig_adjusted = go.Figure()
        for idx, node in enumerate(nodes):
            energies = np.array([atoms.get_potential_energy() for atoms in node.frames])
            energies -= energies[0]
            fig_adjusted.add_trace(
                go.Scatter(
                    x=list(range(len(energies))),
                    y=energies,
                    mode="lines+markers",
                    name=node.name.replace(f"_{node.__class__.__name__}", ""),
                    customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
                )
            )
            offset += len(energies)

        fig_adjusted.update_layout(
            title="Adjusted energy vs. Steps",
            xaxis_title="Step",
            yaxis_title="Adjusted energy",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        fig_adjusted.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
            zeroline=False,
        )
        fig_adjusted.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
            zeroline=False,
        )

        return ComparisonResults(
            frames=frames,
            figures={"energy_vs_steps": fig, "adjusted_energy_vs_steps": fig_adjusted},
        )
