import zntrack
import ase
import numpy as np
from ase.geometry.analysis import Analysis
import pandas as pd

from mlipx.abc import ComparisonResults
import plotly.graph_objects as go



class RadialDistributionFunction(zntrack.Node):
    """Calculate the radial distribution function (RDF).
    
    Parameters
    ----------
    data : list[ase.Atoms]
        List of atomic structures to calculate the RDF for.
    species : tuple[str, str]
        Tuple of species to calculate the RDF for.
    """
    data: list[ase.Atoms] = zntrack.deps()
    species: tuple[str, str] = zntrack.params()
    nbins: int| None = zntrack.params(None)
    rmax: float| None = zntrack.params(None)
    rdf: pd.DataFrame = zntrack.plots()

    def run(self):
        if self.rmax is None:
            # estimate rmax based on the size of the system
            rmax = self.data[0].get_cell().max() / 2
        else:
            rmax = self.rmax
        if self.nbins is None:
            # estimate nbins based on the size of the system
            nbins = int(rmax / 0.01)
        else:
            nbins = self.nbins
        ana = Analysis(self.data)
        rdf = ana.get_rdf(nbins=nbins, rmax=rmax, elements=self.species)
        self.rdf = pd.DataFrame({"r": np.linspace(0, rmax, nbins), "g(r)": np.mean(rdf, axis=0)})
    
    @property
    def frames(self) -> list[ase.Atoms]:
        """Return the frames used to calculate the RDF."""
        return self.data

    @staticmethod
    def compare(*nodes: "RadialDistributionFunction") -> ComparisonResults:
        # frames = sum([node.frames for node in nodes], [])
        frames = [ase.Atoms()]

        fig = go.Figure()
        for node in nodes:
            fig.add_trace(go.Scatter(x=node.rdf["r"], y=node.rdf["g(r)"], mode="lines", name=node.name.replace(f"_{node.__class__.__name__}", ""),))
        
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

        return ComparisonResults(
            frames=frames,
            figures={"rdf": fig},
        )