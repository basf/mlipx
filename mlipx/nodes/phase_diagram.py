# skip linting for this file

import itertools
import os
import typing as t

import ase.io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase.optimize import BFGS
from mp_api.client import MPRester
from pymatgen.analysis.phase_diagram import PDPlotter
from pymatgen.analysis.phase_diagram import PhaseDiagram as pmg_PhaseDiagram
from pymatgen.entries.compatibility import (
    MaterialsProject2020Compatibility,
)
from pymatgen.entries.computed_entries import (
    ComputedEntry,
)

from mlipx.abc import ComparisonResults, NodeWithCalculator


class PhaseDiagram(zntrack.Node):
    """Compute the phase diagram for a given set of structures.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of structures to evaluate.
    model : NodeWithCalculator
        Node providing the calculator object for the energy calculations.
    chemsys:  list[str], defaeult=None
        The set of chemical symbols to construct phase diagram.
    data_ids : list[int], default=None
        Index of the structure to evaluate.
    geo_opt: bool, default=False
        Whether to perform geometry optimization before calculating the
        formation energy of each structure.
    fmax: float, default=0.05
        The maximum force stopping rule for geometry optimizations.

    Attributes
    ----------
    results : pd.DataFrame
        DataFrame with the data_id, potential energy and formation energy.
    plots : dict[str, go.Figure]
        Dictionary with the phase diagram (and formation energy plot).

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    chemsys: list[str] = zntrack.params(None)
    data_ids: list[int] = zntrack.params(None)
    geo_opt: bool = zntrack.params(False)
    fmax: float = zntrack.params(0.05)
    frames_path: str = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    results: pd.DataFrame = zntrack.plots(x="data_id", y="formation_energy")
    phase_diagram: t.Any = zntrack.outs()

    def run(self):  # noqa C901
        if self.data_ids is None:
            atoms_list = self.data
        else:
            atoms_list = [self.data[i] for i in self.data_id]
        if self.model is not None:
            calc = self.model.get_calculator()

        U_metal_set = {"Co", "Cr", "Fe", "Mn", "Mo", "Ni", "V", "W"}
        U_settings = {
            "Co": 3.32,
            "Cr": 3.7,
            "Fe": 5.3,
            "Mn": 3.9,
            "Mo": 4.38,
            "Ni": 6.2,
            "V": 3.25,
            "W": 6.2,
        }
        try:
            api_key = os.environ["MP_API_KEY"]
        except KeyError:
            api_key = None

        entries, epots = [], []
        for atoms in atoms_list:
            metals = [s for s in set(atoms.symbols) if s not in ["O", "H"]]
            hubbards = {}
            if set(metals) & U_metal_set:
                run_type = "GGA+U"
                is_hubbard = True
                for m in metals:
                    hubbards[m] = U_settings.get(m, 0)
            else:
                run_type = "GGA"
                is_hubbard = False

            if self.model is not None:
                atoms.calc = calc
            if self.geo_opt:
                dyn = BFGS(atoms)
                dyn.run(fmax=self.fmax)
            epot = atoms.get_potential_energy()
            ase.io.write(self.frames_path, atoms, append=True)
            epots.append(epot)
            amt_dict = {
                m: len([a for a in atoms if a.symbol == m]) for m in set(atoms.symbols)
            }
            entry = ComputedEntry(
                composition=amt_dict,
                energy=epot,
                parameters={
                    "run_type": run_type,
                    "software": "N/A",
                    "oxide_type": "oxide",
                    "is_hubbard": is_hubbard,
                    "hubbards": hubbards,
                },
            )
            entries.append(entry)
        compat = MaterialsProject2020Compatibility()
        computed_entries = compat.process_entries(entries)
        if api_key is None:
            mp_entries = []
        else:
            mpr = MPRester(api_key)
            if self.chemsys is None:
                chemsys = set(
                    itertools.chain.from_iterable(atoms.symbols for atoms in atoms_list)
                )
            else:
                chemsys = self.chemsys
            mp_entries = mpr.get_entries_in_chemsys(chemsys)
        all_entries = computed_entries + mp_entries
        self.phase_diagram = pmg_PhaseDiagram(all_entries)

        row_dicts = []
        for i, entry in enumerate(computed_entries):
            if self.data_ids is None:
                data_id = i
            else:
                data_id = self.data_id[i]
            eform = self.phase_diagram.get_form_energy_per_atom(entry)
            row_dicts.append(
                {
                    "data_id": data_id,
                    "potential_energy": epots[i],
                    "formation_energy": eform,
                },
            )
        self.results = pd.DataFrame(row_dicts)

    @property
    def figures(self) -> dict[str, go.Figure]:
        plotter = PDPlotter(self.phase_diagram)
        fig1 = plotter.get_plot()
        fig2 = px.line(self.results, x="data_id", y="formation_energy")
        fig2.update_layout(title="Formation Energy Plot")
        pd_df = pd.DataFrame(
            [len(self.phase_diagram.stable_entries)], columns=["Stable_phases"]
        )
        fig3 = px.bar(pd_df, y="Stable_phases")

        return {
            "phase-diagram": fig1,
            "formation-energy-plot": fig2,
            "stable_phases": fig3,
        }

    @staticmethod
    def compare(*nodes: "PhaseDiagram") -> ComparisonResults:
        figures = {}

        for node in nodes:
            # Extract a unique identifier for the node
            node_identifier = node.name.replace(f"_{node.__class__.__name__}", "")

            # Update and store the figures directly
            for key, fig in node.figures.items():
                fig.update_layout(
                    title=node_identifier,
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
                figures[f"{node_identifier}-{key}"] = fig

        return {
            "frames": nodes[0].frames,
            "figures": figures,
        }

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))
