# skip linting for this file

import itertools
import os
import typing as t
import warnings

import ase.io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase.optimize import BFGS
from mp_api.client import MPRester
from plotly.subplots import make_subplots
from pymatgen.analysis.phase_diagram import PDPlotter
from pymatgen.analysis.phase_diagram import PhaseDiagram as pmg_PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram as pmg_PourbaixDiagram
from pymatgen.analysis.pourbaix_diagram import PourbaixEntry, PourbaixPlotter
from pymatgen.core import Element
from pymatgen.core.ion import Ion
from pymatgen.entries.compatibility import (
    MaterialsProject2020Compatibility,
    MaterialsProjectAqueousCompatibility,
)
from pymatgen.entries.computed_entries import (
    ComputedEntry,
    GibbsComputedStructureEntry,
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
        n_nodes = len(nodes)
        n_cols, n_rows = 0, n_nodes
        while n_cols + 1 <= n_rows:
            n_cols += 1
            if n_nodes % n_cols == 0:
                n_rows = n_nodes // n_cols
        trace_type = nodes[0].figures["phase-diagram"].data[0].type
        specs = [[{"type": trace_type} for i in range(n_cols)] for _ in range(n_rows)]

        fig1 = make_subplots(
            rows=n_rows,
            cols=n_cols,
            shared_xaxes=True,
            vertical_spacing=0.2,
            specs=specs,
            subplot_titles=[f"plot_{i}" for i in range(n_nodes)],
        )

        # add each trace (or traces) to its specific subplot
        names = []
        for i, node in enumerate(nodes):
            name = node.name
            names.append(name)
            for trace in node.figures["phase-diagram"].data:
                fig1.add_trace(trace, row=i // n_cols + 1, col=i % n_cols + 1)
        names_map = {f"plot_{i}": names[i] for i in range(n_nodes)}
        fig1.for_each_annotation(lambda x: x.update(text=names_map[x.text]))
        fig1.update_xaxes(showticklabels=False)  # Hide x axis ticks
        fig1.update_yaxes(showticklabels=False)  # Hide y axis ticks
        fig1.update_layout(title="Phase Diagram Comparison")

        fig2 = go.Figure()
        for node in nodes:
            name = node.name
            fig2.add_trace(
                go.Scatter(
                    x=node.results["data_id"],
                    y=node.results["formation_energy"],
                    mode="lines+markers",
                    name=name,
                )
            )
        fig2.update_layout(
            title="Formation Energy Comparison",
            xaxis_title="data_id",
            yaxis_title="formation_energy",
        )

        return {
            "frames": nodes[0].frames,
            "figures": {
                "phase-diagram-comparison": fig1,
                "formation-energy-comparison": fig2,
            },
        }

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))


class PourbaixDiagram(zntrack.Node):
    """Compute the Pourbaix diagram for a given set of structures.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of structures to evaluate.
    model : NodeWithCalculator
        Node providing the calculator object for the energy calculations.
    pH : float
        pH where the Pourbaix stability is evaluated ,
    V : float
        Electrode potential where the Pourbaix stability is evaluated.
    use_gibbs : bool, default=False
        Set to 300 (for 300 Kelvin) to use a machine learning model to
        estimate solid free energy from DFT energy (see
        GibbsComputedStructureEntry). This can slightly improve the accuracy
        of the Pourbaix diagram in some cases. Default: None. Note that
        temperatures other than 300K are not permitted here, because
        MaterialsProjectAqueousCompatibility corrections, used in Pourbaix
        diagram construction, are calculated based on 300 K data.
    data_ids : list[int], default=None
        Index of the structure to evaluate.
    geo_opt: bool, default=False
        Whether to perform geometry optimization before calculating the
        Pourbaix decomposition energy of each structure.
    fmax: float, default=0.05
        The maximum force stopping rule for geometry optimizations.

    Attributes
    ----------
    results : pd.DataFrame
        DataFrame with the data_id, potential energy and Pourbaix
        decomposition energy.
    plots : dict[str, go.Figure]
        Dictionary with the phase diagram (and Pourbaix decomposition
        energy plot).

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    pH: float = zntrack.params()
    V: float = zntrack.params()
    use_gibbs: bool = zntrack.params(False)
    data_ids: list[int] = zntrack.params(None)
    geo_opt: bool = zntrack.params(False)
    fmax: float = zntrack.params(0.05)
    frames_path: str = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    results: pd.DataFrame = zntrack.plots(
        x="data_id", y="pourbaix_decomposition_energy"
    )
    pourbaix_diagram: t.Any = zntrack.outs()

    def run(self):  # noqa: C901
        if self.data_ids is None:
            atoms_list = self.data
        else:
            atoms_list = [self.data[i] for i in self.data_id]
        if self.model is not None:
            calc = self.model.get_calculator()

        try:
            api_key = os.environ["MP_API_KEY"]
        except KeyError:
            raise KeyError("Please set the environment variable `MP_API_KEY`.")

        mpr = MPRester(api_key)
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
        solid_compat = MaterialsProject2020Compatibility()
        chemsys = set(
            itertools.chain.from_iterable(atoms.symbols for atoms in atoms_list)
        )
        # capitalize and sort the elements
        chemsys = sorted(e.capitalize() for e in chemsys)
        if isinstance(chemsys, str):
            chemsys = chemsys.split("-")
        # download the ion reference data from MPContribs
        ion_data = mpr.get_ion_reference_data_for_chemsys(chemsys)
        # build the PhaseDiagram for get_ion_entries
        ion_ref_comps = [
            Ion.from_formula(d["data"]["RefSolid"]).composition for d in ion_data
        ]
        ion_ref_elts = set(
            itertools.chain.from_iterable(i.elements for i in ion_ref_comps)
        )
        # TODO - would be great if the commented line below would work
        # However for some reason you cannot process GibbsComputedStructureEntry with
        # MaterialsProjectAqueousCompatibility
        ion_ref_entries = mpr.get_entries_in_chemsys(
            list([str(e) for e in ion_ref_elts] + ["O", "H"]), use_gibbs=self.use_gibbs
        )

        epots, new_ion_ref_entries, metal_comp_dicts, metallic_ids = [], [], [], []
        for i, atoms in enumerate(atoms_list):
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
            n_metals = len([a for a in atoms if a.symbol not in ["O", "H"]])
            if n_metals > 0:
                metal_comp_dict = {m: amt_dict[m] / n_metals for m in metals}
                metallic_ids.append(i)
                metal_comp_dicts.append(metal_comp_dict)
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
            new_ion_ref_entries.append(entry)
        ion_ref_entries = new_ion_ref_entries + ion_ref_entries
        # suppress the warning about supplying the required energies;
        #  they will be calculated from the
        # entries we get from MPRester
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="You did not provide the required O2 and H2O energies.",
            )
            compat = MaterialsProjectAqueousCompatibility(solid_compat=solid_compat)
        # suppress the warning about missing oxidation states
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Failed to guess oxidation states.*"
            )
            ion_ref_entries = compat.process_entries(ion_ref_entries)  # type: ignore

        # TODO - if the commented line above would work, this conditional block
        # could be removed
        if self.use_gibbs:
            # replace the entries with GibbsComputedStructureEntry
            ion_ref_entries = GibbsComputedStructureEntry.from_entries(
                ion_ref_entries, temp=self.use_gibbs
            )
        ion_ref_pd = pmg_PhaseDiagram(ion_ref_entries)
        ion_entries = mpr.get_ion_entries(ion_ref_pd, ion_ref_data=ion_data)
        pbx_entries = [PourbaixEntry(e, f"ion-{n}") for n, e in enumerate(ion_entries)]

        # Construct the solid pourbaix entries from filtered ion_ref entries
        extra_elts = (
            set(ion_ref_elts)
            - {Element(s) for s in chemsys}
            - {Element("H"), Element("O")}
        )
        new_pbx_entries = []
        for entry in ion_ref_entries:
            entry_elts = set(entry.composition.elements)
            # Ensure no OH chemsys or extraneous elements from ion references
            if not (
                entry_elts <= {Element("H"), Element("O")}
                or extra_elts.intersection(entry_elts)
            ):
                # Create new computed entry
                eform = ion_ref_pd.get_form_energy(entry)  # type: ignore
                new_entry = ComputedEntry(
                    entry.composition, eform, entry_id=entry.entry_id
                )
                pbx_entry = PourbaixEntry(new_entry)
                new_pbx_entries.append(pbx_entry)

        pbx_entries = new_pbx_entries + pbx_entries
        row_dicts = []
        epbx_min = 10000.0
        for i, atoms in enumerate(atoms_list):
            if self.data_ids is None:
                data_id = i
            else:
                data_id = self.data_id[i]
            if i in metallic_ids:
                idx = metallic_ids.index(i)
                entry = pbx_entries[idx]
                pbx_dia = pmg_PourbaixDiagram(
                    pbx_entries, comp_dict=metal_comp_dicts[idx]
                )
                epbx = pbx_dia.get_decomposition_energy(entry, pH=self.pH, V=self.V)
                if epbx < epbx_min:
                    self.pourbaix_diagram = pbx_dia
                    epbx_min = epbx
            else:
                epbx = 0.0
            row_dicts.append(
                {
                    "data_id": data_id,
                    "potential_energy": epots[i],
                    "pourbaix_decomposition_energy": epbx,
                },
            )
        self.results = pd.DataFrame(row_dicts)

    @property
    def figures(self) -> dict[str, go.Figure]:
        plotter = PourbaixPlotter(self.pourbaix_diagram)
        mpl_fig = plotter.get_pourbaix_plot().get_figure()
        mpl_fig.canvas.draw()
        mpl_data = np.frombuffer(mpl_fig.canvas.tostring_rgb(), dtype=np.uint8)
        mpl_data = mpl_data.reshape(mpl_fig.canvas.get_width_height()[::-1] + (3,))
        plt.close()
        fig1 = px.imshow(mpl_data)
        fig2 = px.line(self.results, x="data_id", y="pourbaix_decomposition_energy")
        fig2.update_layout(title="Pourbaix Decomposition Energy Plot")

        return {"pourbaix-diagram": fig1, "pourbaix-decomposition-energy-plot": fig2}

    @staticmethod
    def compare(*nodes: "PourbaixDiagram") -> ComparisonResults:
        n_nodes = len(nodes)
        n_cols, n_rows = 0, n_nodes
        while n_cols + 1 <= n_rows:
            n_cols += 1
            if n_nodes % n_cols == 0:
                n_rows = n_nodes // n_cols
        trace_type = nodes[0].plots["pourbaix-diagram"].data[0].type
        specs = [[{"type": trace_type} for i in range(n_cols)] for _ in range(n_rows)]

        fig1 = make_subplots(
            rows=n_rows,
            cols=n_cols,
            shared_xaxes=True,
            vertical_spacing=0.2,
            specs=specs,
            subplot_titles=[f"plot_{i}" for i in range(n_nodes)],
        )

        # add each trace (or traces) to its specific subplot
        names = []
        for i, node in enumerate(nodes):
            name = node.name
            names.append(name)
            for trace in node.figures["pourbaix-diagram"].data:
                fig1.add_trace(trace, row=i // n_cols + 1, col=i % n_cols + 1)
        names_map = {f"plot_{i}": names[i] for i in range(n_nodes)}
        fig1.for_each_annotation(lambda x: x.update(text=names_map[x.text]))
        fig1.update_xaxes(showticklabels=False)  # Hide x axis ticks
        fig1.update_yaxes(showticklabels=False)  # Hide y axis ticks
        fig1.update_layout(title="Pourbaix Diagram Comparison")

        fig2 = go.Figure()
        for node in nodes:
            name = node.name
            fig2.add_trace(
                go.Scatter(
                    x=node.results["data_id"],
                    y=node.results["pourbaix_decomposition_energy"],
                    mode="lines+markers",
                    name=name,
                )
            )
        fig2.update_layout(
            title="Pourbaix Decomposition Energy Comparison",
            xaxis_title="data_id",
            yaxis_title="poubaix_decomposition_energy",
        )

        return {
            "frames": nodes[0].frames,
            "figures": {
                "pourbaix-diagram-comparison": fig1,
                "pourbaix_decomposition-energy-comparison": fig2,
            },
        }

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))
