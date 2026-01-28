import pathlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import zntrack


class MetadynamicsAnalysis(zntrack.Node):
    """Analyze metadynamics simulation results.

    Reads COLVAR and HILLS files from an ASEMD metadynamics simulation
    and produces collective variable time series and free energy surface plots.

    Parameters
    ----------
    md : zntrack.Node
        The MolecularDynamics node containing the metadynamics simulation.
        Must have been run with a hillclimber MetaDynamicsModel.

    Attributes
    ----------
    cv_data : pd.DataFrame
        Time series of collective variables (phi, psi angles).
    plots_dir : pathlib.Path
        Directory containing PNG plot outputs.
    """

    md: zntrack.Node = zntrack.deps()

    cv_data: pd.DataFrame = zntrack.plots(x="time", y=["phi", "psi"])
    plots_dir: pathlib.Path = zntrack.outs_path(zntrack.nwd / "plots")

    def run(self):
        import hillclimber as hc

        # Access files from MD node's working directory
        md_nwd = pathlib.Path(self.md.nwd)
        colvar_file = md_nwd / "COLVAR"
        hills_file = md_nwd / "HILLS"

        # Read CV time series using hillclimber
        cv_dict = hc.read_colvar(str(colvar_file))
        self.cv_data = pd.DataFrame(cv_dict)

        # Compute FES using hillclimber's sum_hills
        fes_file = pathlib.Path(self.nwd) / "fes.dat"
        hc.sum_hills(
            hills_file=str(hills_file),
            bin=[100, 100],
            min_bounds=[-np.pi, -np.pi],
            max_bounds=[np.pi, np.pi],
            outfile=str(fes_file),
        )

        # Read FES data (format: phi, psi, free_energy, der_phi, der_psi)
        fes_raw = np.loadtxt(fes_file, comments="#")
        fes_data = pd.DataFrame(fes_raw[:, :3], columns=["phi", "psi", "free_energy"])

        # Create plots directory and save PNG plots
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self._save_plots(fes_data)

    def _save_plots(self, fes_data: pd.DataFrame) -> None:
        """Generate and save PNG plots."""
        import matplotlib.pyplot as plt

        # CV time series plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.cv_data["time"], self.cv_data["phi"], label="φ (phi)", linewidth=1)
        ax.plot(self.cv_data["time"], self.cv_data["psi"], label="ψ (psi)", linewidth=1)
        ax.set_xlabel("Time (fs)")
        ax.set_ylabel("Angle (rad)")
        ax.set_title("Collective Variables vs Time")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.savefig(self.plots_dir / "cv_time_series.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Free energy surface (2D heatmap)
        pivot = fes_data.pivot_table(
            index="psi", columns="phi", values="free_energy", aggfunc="mean"
        )

        fig, ax = plt.subplots(figsize=(8, 8))
        im = ax.imshow(
            pivot.values,
            extent=[-np.pi, np.pi, -np.pi, np.pi],
            origin="lower",
            aspect="equal",
            cmap="viridis",
        )
        ax.set_xlabel("φ (rad)")
        ax.set_ylabel("ψ (rad)")
        ax.set_title("Free Energy Surface")
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("Free Energy (eV)")
        fig.savefig(self.plots_dir / "fes.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Ramachandran-style scatter plot
        fig, ax = plt.subplots(figsize=(8, 8))
        scatter = ax.scatter(
            self.cv_data["phi"],
            self.cv_data["psi"],
            c=self.cv_data["time"],
            cmap="viridis",
            s=20,
            alpha=0.7,
        )
        ax.set_xlabel("φ (rad)")
        ax.set_ylabel("ψ (rad)")
        ax.set_title("Ramachandran Plot (φ vs ψ)")
        ax.set_xlim(-np.pi, np.pi)
        ax.set_ylim(-np.pi, np.pi)
        ax.grid(True, alpha=0.3)
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label("Time (fs)")
        fig.savefig(self.plots_dir / "ramachandran.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    @property
    def figures(self) -> dict[str, go.Figure]:
        """Generate plots for CV time series and free energy surface."""
        figures = {}

        # Read FES data for plotting
        fes_file = pathlib.Path(self.nwd) / "fes.dat"
        fes_raw = np.loadtxt(fes_file, comments="#")
        fes_data = pd.DataFrame(fes_raw[:, :3], columns=["phi", "psi", "free_energy"])

        # CV time series plot
        cv_fig = go.Figure()
        cv_fig.add_trace(
            go.Scatter(
                x=self.cv_data["time"],
                y=self.cv_data["phi"],
                mode="lines",
                name="φ (phi)",
                line={"width": 0.5},
            )
        )
        cv_fig.add_trace(
            go.Scatter(
                x=self.cv_data["time"],
                y=self.cv_data["psi"],
                mode="lines",
                name="ψ (psi)",
                line={"width": 0.5},
            )
        )
        cv_fig.update_layout(
            title="Collective Variables vs Time",
            xaxis_title="Time (fs)",
            yaxis_title="Angle (rad)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        cv_fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
        )
        cv_fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
        )
        figures["cv-time-series"] = cv_fig

        # Free energy surface (2D heatmap)
        if fes_data is not None and len(fes_data) > 0:
            pivot = fes_data.pivot_table(
                index="psi", columns="phi", values="free_energy", aggfunc="mean"
            )

            fes_fig = go.Figure(
                data=go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns,
                    y=pivot.index,
                    colorscale="Viridis",
                    colorbar={"title": "Free Energy (eV)"},
                )
            )
            fes_fig.update_layout(
                title="Free Energy Surface",
                xaxis_title="φ (rad)",
                yaxis_title="ψ (rad)",
                plot_bgcolor="rgba(0, 0, 0, 0)",
                paper_bgcolor="rgba(0, 0, 0, 0)",
            )
            figures["free-energy-surface"] = fes_fig

        # Ramachandran-style scatter plot of CV sampling
        rama_fig = go.Figure()
        rama_fig.add_trace(
            go.Scattergl(
                x=self.cv_data["phi"],
                y=self.cv_data["psi"],
                mode="markers",
                marker={"size": 2, "opacity": 0.3, "color": self.cv_data["time"]},
                name="Sampling",
            )
        )
        rama_fig.update_layout(
            title="Ramachandran Plot (φ vs ψ)",
            xaxis_title="φ (rad)",
            yaxis_title="ψ (rad)",
            xaxis={"range": [-np.pi, np.pi]},
            yaxis={"range": [-np.pi, np.pi]},
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )
        rama_fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
        )
        rama_fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(120, 120, 120, 0.3)",
        )
        figures["ramachandran-plot"] = rama_fig

        return figures
