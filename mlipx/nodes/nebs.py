import pathlib
from copy import copy

import ase.io
import ase.optimize
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase.mep import NEB

from mlipx.abc import ComparisonResults, NodeWithCalculator, Optimizer


class NEBinterpolate(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
    n_images: int = zntrack.params(5)
    mic: bool = zntrack.params(False)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "initial_frames.xyz")

    def run(self):
        frames = []
        if len(self.data) == 2:
            atoms = self.data[0]
            for i in range(self.n_images - 1):
                atoms_copy = atoms.copy()
                frames += [atoms_copy]
            atoms_copy = self.data[1]
            frames += [atoms_copy]
        elif len(self.data) == 3:
            atoms0 = self.data[0]
            atoms1 = self.data[1]
            atoms2 = self.data[2]
            ts_index = self.n_images // 2
            for i in range(ts_index - 1):
                atoms_copy = atoms0.copy()
                frames += [atoms_copy]
            for i in range(ts_index, self.n_images):
                atoms_copy = atoms1.copy()
                frames += [atoms_copy]
            atoms_copy = atoms2.copy()
            frames += [atoms_copy]
        neb = NEB(frames)
        neb.interpolate(mic=self.mic)
        ase.io.write(self.frames_path, frames)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))


class NEBs(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
    model: NodeWithCalculator = zntrack.deps()
    relax: bool = zntrack.params(True)
    optimizer: Optimizer = zntrack.params(Optimizer.FIRE.value)
    fmax: float = zntrack.params(0.09)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    trajectory_path: pathlib.Path = zntrack.outs_path(
        zntrack.nwd / "neb_trajectory.traj"
    )
    results: pd.DataFrame = zntrack.plots(y="potential_energy", x="data_id")

    def run(self):
        frames = []
        # neb_trajectory = []
        calc = self.model.get_calculator()
        optimizer = getattr(ase.optimize, self.optimizer)
        for _i in range(len(self.data)):
            atoms_copy = self.data[_i]
            atoms_copy.calc = copy(calc)
            atoms_copy.get_potential_energy()
            frames += [atoms_copy]
        if self.relax is True:
            for i in [0, -1]:
                dyn = optimizer(frames[0])
                dyn.run(fmax=self.fmax)
        neb = NEB(frames, allow_shared_calculator=False)
        dyn = optimizer(neb, trajectory=self.trajectory_path.as_posix())
        dyn.run(fmax=self.fmax)
        ase.io.write(self.frames_path, frames)
        # neb_trajectory = ase.io.read(self.trajectory_path,format="traj",':')
        row_dicts = []
        for i, frame in enumerate(frames):
            row_dicts.append(
                {
                    "data_id": i,
                    "potential_energy": frame.get_potential_energy(),
                    "neb_adjusted_energy": frame.get_potential_energy()
                    - frames[0].get_potential_energy(),
                },
            )
        self.results = pd.DataFrame(row_dicts)

    @property
    def trajectory_frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.trajectory_path, "rb") as f:
            return list(ase.io.iread(f, format="traj"))

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def plots(self) -> dict[str, go.Figure]:
        fig = px.scatter(self.results, x="data_id", y="potential_energy")
        fig.update_layout(title="NEB_path")
        fig.update_traces(customdata=np.stack([np.arange(len(self.results))], axis=1))
        return {"NEB_path": fig}

    @property
    def traj_plots(self) -> dict[str, go.Figure]:
        trajectory_frames = self.trajectory_frames
        total_iterations = len(trajectory_frames) // len(self.frames)
        neb_length = len(self.frames)
        figure = go.Figure()
        for iteration in range(total_iterations):
            images = trajectory_frames[
                iteration * neb_length : (iteration + 1) * neb_length
            ]
            energies = [image.get_potential_energy() for image in images]
            offset = iteration * neb_length
            figure.add_trace(
                go.Scatter(
                    x=list(range(len(energies))),
                    y=energies,
                    mode="lines+markers",
                    name=f"{iteration}",
                    customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
                )
            )
        figure.update_layout(
            title="Energy vs. iteration",
            xaxis_title="image number",
            yaxis_title="Energy",
        )
        return {"energy_vs_iteration": figure}

    @staticmethod
    def compare(*nodes: "NEBs") -> ComparisonResults:
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
            figures={"energy_vs_neb_image": fig},
        )