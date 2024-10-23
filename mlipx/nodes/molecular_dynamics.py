import dataclasses
import pathlib

import ase.io
import ase.units
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tqdm
import zntrack
from ase.md import Langevin

from mlipx.abc import (
    ComparisonResults,
    DynamicsModifier,
    DynamicsObserver,
    NodeWithCalculator,
    NodeWithMolecularDynamics,
)


@dataclasses.dataclass
class LangevinConfig:
    """Configure a Langevin thermostat for molecular dynamics.

    Parameters
    ----------
    timestep : float
        Time step for the molecular dynamics simulation in fs.
    temperature : float
        Temperature of the thermostat.
    friction : float
        Friction coefficient of the thermostat.
    """

    timestep: float
    temperature: float
    friction: float

    def get_molecular_dynamics(self, atoms) -> Langevin:
        return Langevin(
            atoms,
            timestep=self.timestep * ase.units.fs,
            temperature_K=self.temperature,
            friction=self.friction,
        )


class MolecularDynamics(zntrack.Node):
    """Run molecular dynamics simulation.

    Parameters
    ----------
    model : NodeWithCalculator
        Node providing the calculator object for the simulation.
    thermostat : LangevinConfig
        Node providing the thermostat object for the simulation.
    data : list[ase.Atoms]
        Initial configurations for the simulation.
    data_id : int, default=-1
        Index of the initial configuration to use.
    steps : int, default=100
        Number of steps to run the simulation.
    """

    model: NodeWithCalculator = zntrack.deps()
    thermostat: NodeWithMolecularDynamics = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)
    steps: int = zntrack.params(100)
    observers: list[DynamicsObserver] = zntrack.deps(None)
    modifiers: list[DynamicsModifier] = zntrack.deps(None)

    observer_metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots(y=["energy", "fmax"])

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        if self.observers is None:
            self.observers = []
        atoms = self.data[self.data_id]
        atoms.calc = self.model.get_calculator()
        dyn = self.thermostat.get_molecular_dynamics(atoms)
        for obs in self.observers:
            obs.initialize(atoms)

        self.observer_metrics = {}

        for idx, _ in enumerate(
            tqdm.tqdm(dyn.irun(steps=self.steps), total=self.steps)
        ):
            ase.io.write(self.frames_path, atoms, append=True)
            self.state.extend_plots(
                "plots",
                {
                    "energy": atoms.get_potential_energy(),
                    "fmax": np.max(np.linalg.norm(atoms.get_forces(), axis=1)),
                    "fnorm": np.linalg.norm(atoms.get_forces()),
                },
            )
            for obs in self.observers:
                if obs.check(atoms):
                    self.observer_metrics[obs.name] = idx

            if len(self.observer_metrics) > 0:
                break

            for mod in self.modifiers:
                mod.modify(dyn, idx)

        for obs in self.observers:
            # document all attached observers
            self.observer_metrics[obs.name] = self.observer_metrics.get(obs.name, -1)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def figures(self) -> dict[str, go.Figure]:
        plots = {}
        for key in self.plots.columns:
            fig = px.line(
                self.plots,
                x=self.plots.index,
                y=key,
                title=key,
            )
            fig.update_traces(
                customdata=np.stack([np.arange(len(self.plots))], axis=1),
            )
            plots[key] = fig
        return plots

    @staticmethod
    def compare(*nodes: "MolecularDynamics") -> ComparisonResults:
        frames = sum([node.frames for node in nodes], [])
        offset = 0
        fig = go.Figure()
        for _, node in enumerate(nodes):
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