import pathlib

import ase.io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase import units
from ase.constraints import FixAtoms
from ase.thermochemistry import HarmonicThermo
from ase.vibrations import Vibrations

# from copy import deepcopy
from tqdm import tqdm

from mlipx.abc import ComparisonResults, NodeWithCalculator


class VibrationalAnalysis(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
    # image_ids: list[int] = zntrack.params()
    model: NodeWithCalculator = zntrack.deps()
    # adding more parameters
    # n_images: int = zntrack.params(5)
    # fmax: float = zntrack.params(0.09)
    displacement: float = zntrack.params(0.01)
    nfree: int = zntrack.params(4)
    lower_freq_threshold: float = zntrack.params(12.0)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")
    modes_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "modes.xyz")
    modes_cache: pathlib.Path = zntrack.outs_path(zntrack.nwd / "modes")
    vib_cache: pathlib.Path = zntrack.outs_path(zntrack.nwd / "vib")
    results: pd.DataFrame = zntrack.plots(y="ddG_300k", x="Frame")

    def run(self):
        # frames = []
        # molecules = {}
        calc = self.model.get_calculator()
        results = []  # {"Frame": [], "ddG_300k": []}
        modes = []

        for current_frame, atoms in tqdm(enumerate(self.data)):
            # these type/molecule checks should go into a separate node.
            if (
                "type" not in atoms.info
                or "molecule_indices" not in atoms.info
                or atoms.info["type"].lower() not in ["slab+adsorbate", "slab+ads"]
            ):
                continue

            cache = self.vib_cache / f"{current_frame}"
            cache.mkdir(parents=True, exist_ok=True)

            modes_cache = self.modes_cache / f"{current_frame}"
            modes_cache.mkdir(parents=True, exist_ok=True)

            constraints = [
                i
                for i, j in enumerate(atoms)
                if i not in atoms.info["molecule_indices"]
            ]
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
                indices=atoms.info["molecule_indices"],
            )
            vib.run()
            _freq = vib.get_frequencies()

            freq = [
                i
                if i > self.lower_freq_threshold
                else complex(self.lower_freq_threshold)
                for i in _freq
            ]

            if atoms.info["calc_type"] == "relax":
                pass

            elif atoms.info["calc_type"] == "ts":
                freq = freq[1:]
                # freq[0] = _freq[0]

            vib_energies = [i * 0.0001239843 for i in freq]

            thermo = HarmonicThermo(vib_energies=vib_energies, potentialenergy=0.0)

            dg_300k = thermo.get_helmholtz_energy(300, verbose=True)
            atoms.info["dg_300.0k"] = dg_300k

            # results["Frame"].append(current_frame)
            # results["ddG_300k"].append(dg_300k)

            results.append({"Frame": current_frame, "ddG_300k": dg_300k})

            for temp in np.linspace(10, 1000, 10):
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

            for mode in range(len(atoms.info["molecule_indices"]) * 3):
                mode_cache = modes_cache / f"mode_{mode}.traj"
                kT = units.kB * 300
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
    def plots(self) -> dict[str, go.Figure]:
        # plotter = PDPlotter(self.pd)
        # fig = plotter.get_plot()
        fig = px.line(self.results, x="Frame", y="ddG_300k", markers=True)
        fig.update_layout(
            title="Gibbs Free Energy at 300K",
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
                    y=node.results["ddG_300k"],
                    mode="lines+markers",
                    name=node.name,
                    customdata=np.stack(
                        [np.arange(len(node.results["ddG_300k"])) + offset], axis=1
                    ),
                )
            )
            offset += len(node.results["ddG_300k"])

        fig.update_layout(
            title="Comparison of Gibbs Free Energies at 300K",
            xaxis_title="Frame",
            yaxis_title="ddG (eV)",
        )

        return ComparisonResults(frames=frames, figures={"Gibbs-Comparison": fig})
