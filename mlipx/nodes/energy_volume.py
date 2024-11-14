import ase.io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tqdm
import zntrack

from mlipx.abc import ComparisonResults, NodeWithCalculator


class EnergyVolumeCurve(zntrack.Node):
    """Compute the energy-volume curve for a given structure.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of structures to evaluate.
    model : NodeWithCalculator
        Node providing the calculator object for the energy calculations.
    data_id : int, default=-1
        Index of the structure to evaluate.
    n_points : int, default=50
        Number of points to sample for the volume scaling.
    start : float, default=0.75
        Initial scaling factor from the original cell.
    stop : float, default=2.0
        Final scaling factor from the original cell.

    Attributes
    ----------
    results : pd.DataFrame
        DataFrame with the volume, energy, and scaling factor.

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)

    n_points: int = zntrack.params(50)
    start: float = zntrack.params(0.75)
    stop: float = zntrack.params(2.0)

    frames_path: str = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    results: pd.DataFrame = zntrack.plots(y="energy", x="scale")

    def run(self):
        atoms = self.data[self.data_id]
        calc = self.model.get_calculator()

        results = []

        scale_factor = np.linspace(self.start, self.stop, self.n_points)
        for scale in tqdm.tqdm(scale_factor):
            atoms_copy = atoms.copy()
            atoms_copy.set_cell(atoms.get_cell() * scale, scale_atoms=True)
            atoms_copy.calc = calc

            results.append(
                {
                    "volume": atoms_copy.get_volume(),
                    "energy": atoms_copy.get_potential_energy(),
                    "fmax": np.linalg.norm(atoms_copy.get_forces(), axis=-1).max(),
                    "scale": scale,
                }
            )

            ase.io.write(self.frames_path, atoms_copy, append=True)

        self.results = pd.DataFrame(results)

    @property
    def frames(self) -> list[ase.Atoms]:
        """List of structures evaluated during the energy-volume curve."""
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def figures(self) -> dict[str, go.Figure]:
        """Plot the energy-volume curve."""
        fig = px.scatter(self.results, x="scale", y="energy", color="scale")
        fig.update_layout(title="Energy-Volume Curve")
        fig.update_traces(customdata=np.stack([np.arange(self.n_points)], axis=1))
        fig.update_xaxes(title_text="cell vector scale")
        fig.update_yaxes(title_text="Energy / eV")

        ffig = px.scatter(self.results, x="scale", y="fmax", color="scale")
        ffig.update_layout(title="Energy-Volume Curve (fmax)")
        ffig.update_traces(customdata=np.stack([np.arange(self.n_points)], axis=1))
        ffig.update_xaxes(title_text="cell vector scale")
        ffig.update_yaxes(title_text="Maximum Force / eV/Å")

        return {"energy-volume-curve": fig, "fmax-volume-curve": ffig}

    @staticmethod
    def compare(*nodes: "EnergyVolumeCurve") -> ComparisonResults:
        """Compare the energy-volume curves of multiple nodes."""
        fig = go.Figure()
        for node in nodes:
            fig.add_trace(
                go.Scatter(
                    x=node.results["scale"],
                    y=node.results["energy"],
                    mode="lines+markers",
                    name=node.name.replace("_EnergyVolumeCurve", ""),
                )
            )
            fig.update_traces(customdata=np.stack([np.arange(node.n_points)], axis=1))

        # TODO: remove all info from the frames?
        # What about forces / energies? Update the key?
        fig.update_layout(title="Energy-Volume Curve Comparison")
        # set x-axis title
        # fig.update_xaxes(title_text="Volume / Å³")
        fig.update_xaxes(title_text="cell vector scale")
        fig.update_yaxes(title_text="Energy / eV")

        # Now adjusted

        fig_adjust = go.Figure()
        for node in nodes:
            scale_factor = np.linspace(node.start, node.stop, node.n_points)
            one_idx = np.abs(scale_factor - 1).argmin()
            fig_adjust.add_trace(
                go.Scatter(
                    x=node.results["volume"],
                    y=node.results["energy"] - node.results["energy"].iloc[one_idx],
                    mode="lines+markers",
                    name=node.name.replace("_EnergyVolumeCurve", ""),
                )
            )
            fig_adjust.update_traces(
                customdata=np.stack([np.arange(node.n_points)], axis=1)
            )

        fig_adjust.update_layout(title="Adjusted Energy-Volume Curve Comparison")
        fig_adjust.update_xaxes(title_text="Volume / Å³")
        fig_adjust.update_yaxes(title_text="Adjusted Energy / eV")

        return {
            "frames": nodes[0].frames,
            "figures": {
                "energy-volume-curve": fig,
                "adjusted_energy-volume-curve": fig_adjust,
            },
        }
