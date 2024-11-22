import contextlib

import ase
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tqdm
import zntrack
from ase.calculators.calculator import PropertyNotImplementedError

from mlipx.abc import ComparisonResults
from mlipx.utils import shallow_copy_atoms


def get_figure(key: str, nodes: list["EvaluateCalculatorResults"]) -> go.Figure:
    fig = go.Figure()
    for node in nodes:
        fig.add_trace(
            go.Scatter(
                x=node.plots.index,
                y=node.plots[key],
                mode="lines+markers",
                name=node.name.replace(f"_{node.__class__.__name__}", ""),
            )
        )
    fig.update_traces(customdata=np.stack([np.arange(len(node.plots.index))], axis=1))
    fig.update_layout(
        title=key,
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
    return fig


class EvaluateCalculatorResults(zntrack.Node):
    """
    Evaluate the results of a calculator.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of atoms objects.

    """

    data: list[ase.Atoms] = zntrack.deps()
    plots: pd.DataFrame = zntrack.plots(
        y=["fmax", "fnorm", "energy"], independent=True, autosave=True
    )

    def run(self):
        self.plots = pd.DataFrame()
        frame_data = []
        for idx in tqdm.tqdm(range(len(self.data))):
            atoms = self.data[idx]

            forces = atoms.get_forces()
            fmax = np.max(np.linalg.norm(forces, axis=1))
            fnorm = np.linalg.norm(forces)
            energy = atoms.get_potential_energy()
            # eform = atoms.info.get(ASEKeys.formation_energy.value, -1)
            n_atoms = len(atoms)

            # have energy and formation energy in the plot

            plots = {
                "fmax": fmax,
                "fnorm": fnorm,
                "energy": energy,
                # "eform": eform,
                "n_atoms": n_atoms,
                "energy_per_atom": energy / n_atoms,
                # "eform_per_atom": eform / n_atoms,
            }
            frame_data.append(plots)
        self.plots = pd.DataFrame(frame_data)

    @property
    def frames(self):
        return self.data

    def __run_note__(self) -> str:
        return f"""# {self.name}
Results from {self.state.remote} at {self.state.rev}.

View the trajectory via zndraw:
```bash
zndraw {self.name}.frames --rev {self.state.rev} --remote {self.state.remote} --url https://app-dev.roqs.basf.net/zndraw_app
```
"""

    @property
    def figures(self) -> dict:
        # TODO: remove index column

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
    def compare(
        *nodes: "EvaluateCalculatorResults", reference: str | None = None
    ) -> ComparisonResults:
        # TODO: if reference, shift energies by
        # rmse(val, reference) and plot as energy_adjusted
        figures = {}
        frames_info = {}
        for key in nodes[0].plots.columns:
            if not all(key in node.plots.columns for node in nodes):
                raise ValueError(f"Key {key} not found in all nodes")
            # check frames are the same
            figures[key] = get_figure(key, nodes)

        for node in nodes:
            for key in node.plots.columns:
                frames_info[f"{node.name}_{key}"] = node.plots[key].values

            # TODO: calculate the rmse difference between a fixed one
            # and all the others and shift them accordingly
            # and plot as energy_shifted

            # plot error between curves
            # mlipx pass additional flags to compare function
            # have different compare methods also for correlation plots

        frames = [shallow_copy_atoms(x) for x in nodes[0].frames]
        for key, values in frames_info.items():
            for atoms, value in zip(frames, values):
                atoms.info[key] = value

        for node in nodes:
            for node_atoms, atoms in zip(node.frames, frames):
                if len(node_atoms) != len(atoms):
                    raise ValueError("Atoms objects have different lengths")
                with contextlib.suppress(RuntimeError, PropertyNotImplementedError):
                    atoms.info[f"{node.name}_energy"] = (
                        node_atoms.get_potential_energy()
                    )
                    atoms.arrays[f"{node.name}_forces"] = node_atoms.get_forces()

        return {
            "frames": frames,
            "figures": figures,
        }
