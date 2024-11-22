import functools
import typing as t

import ase
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import tqdm
import zntrack
from ase.data import atomic_numbers, covalent_radii

from mlipx.abc import ComparisonResults, NodeWithCalculator
from mlipx.utils import freeze_copy_atoms


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
    data : list[ase.Atoms]|None
        Optional list of ase.Atoms. Diatomics for each element in
        this list will be added to `elements`.

    Attributes
    ----------
    frames : list[ase.Atoms]
        List of frames with the bond length varied.
    results : pd.DataFrame
        DataFrame with the energy values for each bond length.
    """

    model: NodeWithCalculator = zntrack.deps()
    elements: list[str] = zntrack.params(("H", "He", "Li"))
    data: list[ase.Atoms] | None = zntrack.deps(None)

    n_points: int = zntrack.params(100)
    min_distance: float = zntrack.params(0.5)
    max_distance: float = zntrack.params(2.0)
    eq_distance: t.Union[t.Literal["covalent-radiuis"], float] = zntrack.params(
        "covalent-radiuis"
    )

    frames: list[ase.Atoms] = zntrack.outs()  # TODO: change to h5md out
    results: pd.DataFrame = zntrack.plots()

    def build_molecule(self, element, distance) -> ase.Atoms:
        return ase.Atoms([element, element], positions=[(0, 0, 0), (0, 0, distance)])

    def run(self):
        self.frames = []
        self.results = pd.DataFrame()
        calc = self.model.get_calculator()
        e_v = {}

        elements = set(self.elements)
        if self.data is not None:
            for atoms in self.data:
                elements.update(set(atoms.symbols))

        for element in elements:
            energies = []
            if self.eq_distance == "covalent-radiuis":
                # convert element to atomic number
                distances = np.linspace(
                    self.min_distance * covalent_radii[atomic_numbers[element]],
                    self.max_distance * covalent_radii[atomic_numbers[element]],
                    self.n_points,
                )
            else:
                distances = np.linspace(
                    self.min_distance, self.max_distance, self.n_points
                )
            tbar = tqdm.tqdm(
                distances, desc=f"{element}-{element} bond ({distances[0]:.2f} Å)"
            )
            for distance in tbar:
                tbar.set_description(f"{element}-{element} bond ({distance:.2f} Å)")
                molecule = self.build_molecule(element, distance)
                molecule.calc = calc
                energies.append(molecule.get_potential_energy())
                self.frames.append(freeze_copy_atoms(molecule))
            e_v[element] = pd.DataFrame(energies, index=distances, columns=[element])
        self.results = functools.reduce(
            lambda x, y: pd.merge(x, y, left_index=True, right_index=True, how="outer"),
            e_v.values(),
        )

    @property
    def figures(self) -> dict:
        # return a plot for each element
        plots = {}
        for element in self.elements:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=self.results[element].dropna().index,
                    y=self.results[element].dropna(),
                    mode="lines",
                )
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

    @classmethod
    def compare(cls, *nodes: "HomonuclearDiatomics") -> ComparisonResults:
        """Compare the energy-bondlength curves for homonuclear diatomic molecules.

        Parameters
        ----------
        nodes : HomonuclearDiatomics
            Nodes to compare.

        Returns
        -------
        ComparisonResults
            Comparison results.
        """
        figures = {}
        for node in nodes:
            for element in node.elements:
                # check if a figure for this element already exists
                if f"{element}-{element} bond" not in figures:
                    # create a line plot and label it with node.name
                    fig = go.Figure()
                    fig.update_layout(title=f"{element}-{element} bond")
                    fig.update_xaxes(title="Distance / Å")
                    fig.update_yaxes(title="Energy / eV")
                else:
                    fig = figures[f"{element}-{element} bond"]

                # add a line plot node.results[element] vs node.results.index
                fig.add_trace(
                    go.Scatter(
                        x=node.results[element].dropna().index,
                        y=node.results[element].dropna(),
                        mode="lines",
                        name=node.name.replace(f"_{cls.__name__}", ""),
                    )
                )
                figures[f"{element}-{element} bond"] = fig

                # Now with adjusted

                # check if a figure for this element already exists
                if f"{element}-{element} bond (adjusted)" not in figures:
                    # create a line plot and label it with node.name
                    fig = go.Figure()
                    fig.update_layout(title=f"{element}-{element} bond")
                    fig.update_xaxes(title="Distance / Å")
                    fig.update_yaxes(title="Adjusted energy / eV")
                else:
                    fig = figures[f"{element}-{element} bond (adjusted)"]

                # find the closest to the cov. dist. index to set the energy to zero
                one_idx = np.abs(
                    node.results[element].dropna().index
                    - covalent_radii[atomic_numbers[element]]
                ).argmin()

                # add a line plot node.results[element] vs node.results.index
                fig.add_trace(
                    go.Scatter(
                        x=node.results[element].dropna().index,
                        y=node.results[element].dropna()
                        - node.results[element].dropna().iloc[one_idx],
                        mode="lines",
                        name=node.name.replace(f"_{cls.__name__}", ""),
                    )
                )
                figures[f"{element}-{element} bond (adjusted)"] = fig

        return {"frames": nodes[0].frames, "figures": figures}
