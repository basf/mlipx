import pathlib
import typing as t

import ase.io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase import units
from ase.constraints import FixAtoms
from ase.thermochemistry import HarmonicThermo, IdealGasThermo
from ase.vibrations import Vibrations

# from copy import deepcopy
from tqdm import tqdm

from mlipx.abc import ComparisonResults, NodeWithCalculator


class VibrationalAnalysis(zntrack.Node):
    """
    Vibrational Analysis Node
    This node performs vibrational analysis on the provided images.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of images to perform vibrational analysis on.
    model : NodeWithCalculator
        Model node with calculator to perform vibrational analysis.
    displacement : float
        Displacement for vibrational analysis.
    nfree : int
        Number of free atoms.
    lower_freq_threshold : float
        Lower frequency threshold.
    frames_path : pathlib.Path
        Path to save frames.
    modes_path : pathlib.Path
        Path to save vibrational modes.
    modes_cache : pathlib.Path
        Path to save modes cache.
    vib_cache : pathlib.Path
        Path to save vibrational cache.

    Attributes
    ----------
    results : pd.DataFrame
        Results of vibrational analysis.
    """

    data: list[ase.Atoms] = zntrack.deps()
    # image_ids: list[int] = zntrack.params()
    model: NodeWithCalculator = zntrack.deps()
    # adding more parameters
    # n_images: int = zntrack.params(5)
    # fmax: float = zntrack.params(0.09)
    displacement: float = zntrack.params(0.01)
    nfree: int = zntrack.params(4)
    temperature: float = zntrack.params(298.15)  # in Kelvin
    lower_freq_threshold: float = zntrack.params(12.0)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    modes_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "modes.xyz")
    modes_cache: pathlib.Path = zntrack.outs_path(zntrack.nwd / "modes")
    vib_cache: pathlib.Path = zntrack.outs_path(zntrack.nwd / "vib")
    results: pd.DataFrame = zntrack.plots(y="ddG", x="Frame")

    free_indices: list[int] = zntrack.params(None)
    # by default freeze no index

    system: (
        t.Literal["molecule"]
        | t.Literal["other"]
        | t.Literal["linear-molecule"]
        | t.Literal["isolated-atom"]
        | None
    ) = zntrack.params(None)
    calc_type: t.Literal["ts"] | t.Literal["relax"] | None = zntrack.params(None)

    def run(self):  # noqa C901
        # frames = []
        # molecules = {}
        calc = self.model.get_calculator()
        results = []  # {"Frame": [], "ddG_300k": []}
        modes = []

        for current_frame, atoms in tqdm(enumerate(self.data)):
            # these type/molecule checks should go into a separate node.
            if self.system is None:
                try:
                    system = atoms.info["type"]  # raises IndexError if neither is set
                except KeyError:
                    raise KeyError(
                        "Unable to determine system type from `atoms.info`."
                        " Please set the 'system' parameter."
                    )
            else:
                system = self.system

            print(system)

            if self.free_indices is None:
                if "free_indices" in atoms.info:
                    free_indices = atoms.info["free_indices"]
                else:
                    free_indices = list(range(len(atoms)))
            else:
                free_indices = self.free_indices

            print(free_indices)

            if self.calc_type is None:
                if "calc_type" in atoms.info:
                    calc_type = atoms.info["calc_type"]
                else:
                    calc_type = "relax"
            else:
                calc_type = self.calc_type

            print(calc_type)

            # if (
            #    "type" not in atoms.info
            #    or "calc_type" not in atoms.info
            #    or "free_indices" not in atoms.info
            #    # or atoms.info["type"].lower() not in ["slab+adsorbate", "slab+ads"]
            # ):
            #    continue

            cache = self.vib_cache / f"{current_frame}"
            cache.mkdir(parents=True, exist_ok=True)

            modes_cache = self.modes_cache / f"{current_frame}"
            modes_cache.mkdir(parents=True, exist_ok=True)

            constraints = [i for i, j in enumerate(atoms) if i not in free_indices]
            c = FixAtoms(constraints)
            atoms.constraints = c

            atoms.calc = calc
            _ = atoms.get_potential_energy()
            _ = atoms.get_forces()
            # fmax = np.linalg.norm(f, axis=1).max()

            vib = Vibrations(
                atoms,
                nfree=self.nfree,
                name=cache,
                delta=self.displacement,
                indices=free_indices,
            )
            vib.run()
            _freq = vib.get_frequencies()

            freq = [
                i
                if i > self.lower_freq_threshold
                else complex(self.lower_freq_threshold)
                for i in _freq
            ]

            if calc_type.lower() == "ts":
                freq = freq[1:]

            if system.lower() in [
                "mol",
                "molecule",
                "linear-molecule",
                "isolated-atom",
            ]:
                if system.lower() == "linear-molecule":
                    freq = freq[5:]
                    geometry = "linear"

                elif system.lower() == "isolated-atom":
                    freq = []
                    geometry = "monatomic"

                else:
                    freq = freq[6:]
                    geometry = "nonlinear"

                vib_energies = [i * 0.0001239843 for i in freq]

                symm_number = 1
                p_pascal = 1e5
                spin = 0

                if "symmetry_number" in atoms.info:
                    symm_number = atoms.info["symmetry_number"]
                if "pressure" in atoms.info:
                    p_pascal = atoms.info["pressure"] * 1e5
                if "spin" in atoms.info:
                    spin = atoms.info["spin"]

                thermo = IdealGasThermo(
                    atoms=atoms,
                    vib_energies=vib_energies,
                    geometry=geometry,
                    potentialenergy=0.0,
                    symmetrynumber=symm_number,
                    spin=spin,
                )
                dg_Tk = thermo.get_gibbs_energy(
                    self.temperature, p_pascal, verbose=True
                )

            else:
                vib_energies = [i * 0.0001239843 for i in freq]
                thermo = HarmonicThermo(vib_energies=vib_energies, potentialenergy=0.0)
                dg_Tk = thermo.get_helmholtz_energy(self.temperature, verbose=True)

            atoms.info[f"dg_{self.temperature}k"] = dg_Tk

            # results["Frame"].append(current_frame)
            # results["ddG_300k"].append(dg_300k)

            results.append({"Frame": current_frame, "ddG": dg_Tk})

            for temp in np.linspace(10, 1000, 10):
                if system.lower() in [
                    "mol",
                    "molecule",
                    "linear-molecule",
                    "isolated-atom",
                ]:
                    dg = thermo.get_gibbs_energy(temp, p_pascal, verbose=True)
                else:
                    dg = thermo.get_helmholtz_energy(temp, verbose=True)

                atoms.info[f"dg_{temp:.1f}k"] = dg
            # vibenergies=vib.get_energies()
            # vib.summary(log='vib.txt')
            # for mode in range(len(vibindices)*3):
            #    vib.write_mode(mode)

            # molecule vibrations disabled for now
            # molecule = atoms.copy()[atoms.info["molecule_indices"]]

            # if molecule.get_chemical_formula() not in molecules:
            #    molecule.calc = calc
            #    molecules[molecule.get_chemical_formula()] = []

            # frames += [atoms]
            ase.io.write(self.frames_path, atoms, append=True)

            for mode in range(len(free_indices) * 3):
                mode_cache = modes_cache / f"mode_{mode}.traj"
                kT = units.kB * self.temperature
                with ase.io.Trajectory(mode_cache, "w") as traj:
                    for image in vib.get_vibrations().iter_animated_mode(
                        mode, temperature=kT, frames=30
                    ):
                        traj.write(image)
                vib_mode = ase.io.read(mode_cache, index=":")
                modes += vib_mode
            #    vib.write_mode(mode)

        ase.io.write(self.modes_path, modes)
        self.results = pd.DataFrame(results)
        # ase.io.write(self.frames_path, frames)

    # run the NEB using self.data, self.image_ids, self.n_images
    # save the trajectroy to self.frames_path
    #
    # ase.io.write(self.frames_path, self.data)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def modes(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.modes_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def figures(self) -> dict[str, go.Figure]:
        # plotter = PDPlotter(self.pd)
        # fig = plotter.get_plot()
        fig = px.line(self.results, x="Frame", y="ddG", markers=True)
        fig.update_layout(
            title=f"Gibbs Free Energy at {self.temperature}K",
            xaxis_title="Frame",
            yaxis_title="ddG (eV)",
        )
        fig.update_traces(customdata=np.stack([np.arange(len(self.results))], axis=-1))
        return {"Gibbs": fig}

    @staticmethod
    def compare(*nodes: "VibrationalAnalysis") -> ComparisonResults:
        frames = sum([node.frames for node in nodes], [])
        offset = 0
        fig = go.Figure()  # px.scatter()
        for i, node in enumerate(nodes):
            fig.add_trace(
                go.Scatter(
                    x=node.results["Frame"],
                    y=node.results["ddG"],
                    mode="lines+markers",
                    name=node.name,
                    customdata=np.stack(
                        [np.arange(len(node.results["ddG"])) + offset], axis=1
                    ),
                )
            )
            offset += len(node.results["ddG"])
            temperature = node.temperature
        fig.update_layout(
            title=f"Comparison of Gibbs Free Energies at {temperature}K",
            xaxis_title="Frame",
            yaxis_title="ddG (eV)",
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

        return ComparisonResults(frames=frames, figures={"Gibbs-Comparison": fig})
