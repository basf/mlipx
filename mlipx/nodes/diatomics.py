import dataclasses

import ase
import numpy as np
import pandas as pd
import plotly.express as px
import tqdm
import zntrack

from mlipx.abc import NodeWithCalculator
from mlipx.utils import freeze_copy_atoms


@dataclasses.dataclass
class HomonuclearDiatomics(zntrack.Node):
    """Compute energy-bondlength curves for homonuclear diatomic molecules.

    Parameters
    ----------
    elements : list[str]
        List of elements to consider. For example, ["H", "He", "Li"].
    model : NodeWithCalculator
        Node providing the calculator object for the energy calculations.
    n_points : int, default=100
        Number of points to sample for the bond length between
        min_distance and max_distance.
    min_distance : float, default=0.5
        Minimum bond length to consider in Angstrom.
    max_distance : float, default=2.0
        Maximum bond length to consider in Angstrom.

    Attributes
    ----------
    frames : list[ase.Atoms]
        List of frames with the bond length varied.
    results : pd.DataFrame
        DataFrame with the energy values for each bond length.
    """

    model: NodeWithCalculator = zntrack.deps()
    elements: list[str] = zntrack.params(("H", "He", "Li"))

    n_points: int = zntrack.params(100)
    min_distance: float = zntrack.params(0.5)
    max_distance: float = zntrack.params(2.0)

    frames: list[ase.Atoms] = zntrack.outs()  # TODO: change to h5md out
    results: pd.DataFrame = zntrack.plots()

    def build_molecule(self, element, distance) -> ase.Atoms:
        return ase.Atoms([element, element], positions=[(0, 0, 0), (0, 0, distance)])

    def run(self):
        self.frames = []
        distances = np.linspace(self.min_distance, self.max_distance, self.n_points)
        self.results = pd.DataFrame(index=distances, columns=self.elements)
        calc = self.model.get_calculator()
        for element in self.elements:
            energies = []
            for distance in tqdm.tqdm(distances, desc=f"{element}-{element} bond"):
                molecule = self.build_molecule(element, distance)
                molecule.calc = calc
                energies.append(molecule.get_potential_energy())
                self.frames.append(freeze_copy_atoms(molecule))
                self.state.extend_plots(
                    "results", {element: energies[-1], "distance": distance}
                )

    @property
    def plots(self) -> dict:
        # return a plot for each element
        plots = {}
        for element in self.elements:
            fig = px.line(
                self.results,
                x=self.results.index,
                y=element,
                title=f"{element}-{element} bond",
            )
            offset = 0
            for prev_element in self.elements:
                if prev_element == element:
                    break
                offset += self.n_points

            fig.update_traces(
                customdata=np.stack([np.arange(self.n_points) + offset], axis=1),
            )
            plots[f"{element}-{element} bond"] = fig
        return plots
