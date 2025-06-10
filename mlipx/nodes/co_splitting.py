import json
import os
import pathlib

import ase.io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zntrack
from ase import Atom, Atoms
from ase.build import molecule, surface
from ase.constraints import FixAtoms, FixedLine
from ase.data import atomic_numbers, covalent_radii
from ase.geometry import get_distances
from ase.io import read, write
from ase.optimize import BFGS
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# from copy import deepcopy
from tqdm import tqdm

from mlipx.abc import ComparisonResults, NodeWithCalculator


def gas_phase(mol, vacuum=10):
    return molecule(mol, vacuum=vacuum)


def gen_surf(atoms, miller=(1, 1, 1), layers=8, vacuum=10, supercell=[2, 2, 1]):
    surf = surface(atoms, miller, layers, vacuum=vacuum, periodic=True)
    surf.center(vacuum=vacuum, axis=2)

    return surf.repeat(supercell)


def drop_atom(current_pos, atoms, R):
    while True:
        distance_matrix = get_distances(
            current_pos, atoms.positions, cell=atoms.cell, pbc=True
        )[1]

        drop = distance_matrix.min() / (4 * R.max())

        n_top_covalent_bonds = np.sum(distance_matrix < R)
        n_valley_covalent_bonds = np.sum(distance_matrix < R * 1.2)

        if n_top_covalent_bonds > 0 or n_valley_covalent_bonds > 1:
            break

        current_pos -= np.array([0, 0, drop])

    return current_pos


def grid_placement(atoms, atom="C", grid_step=0.4):
    _atoms = atoms.copy()
    cell = _atoms.cell

    x = np.arange(0, cell[0, 0], grid_step)
    y = np.arange(0, cell[1, 1], grid_step)

    height = cell[2, 2]

    R_atom = covalent_radii[atomic_numbers[atom]]

    R = np.array(
        [covalent_radii[atomic_numbers[symbol]] + R_atom for symbol in _atoms.symbols]
    )

    pos = []

    for i in x:
        for j in y:
            current_pos = np.array(
                [
                    i + j * (cell[1, 0] / cell[1, 1]),
                    j + i * (cell[0, 1] / cell[0, 0]),
                    height,
                ]
            )
            current_pos = drop_atom(current_pos, _atoms, R)
            pos.append(current_pos)

    _atoms += Atoms(symbols=["X"] * len(pos), positions=pos)

    return pos, _atoms


def relocate_atom(atoms, idx):
    atoms = atoms.copy()
    _atoms = atoms.copy()
    _atoms.set_constraint()
    del _atoms[idx]
    atom = atoms[idx]

    current_pos = atom.position

    R_atom = covalent_radii[atomic_numbers[atom.symbol]]
    R = np.array(
        [covalent_radii[atomic_numbers[symbol]] + R_atom for symbol in _atoms.symbols]
    )

    current_pos = drop_atom(current_pos, _atoms, R)

    atoms[idx].position = current_pos

    return atoms


def gen_images(atoms, pos, mol="C"):
    traj = []
    for xyz in pos:
        _atoms = atoms.copy()
        if mol == "CO":
            _atoms += Atoms(
                symbols=["C", "O"], positions=[xyz, xyz + np.array([0, 0, 1.2])]
            )

        elif mol == "COH":
            _atoms += Atoms(
                symbols=["C", "O", "H"],
                positions=[
                    xyz,
                    xyz + np.array([0, 0, 1.2]),
                    xyz + np.array([0, 0.8, 2.0]),
                ],
            )

        elif mol == "OH":
            _atoms += Atoms(
                symbols=["O", "H"], positions=[xyz, xyz + np.array([0, 0.8, 0.8])]
            )

        else:
            _atoms.append(Atom(mol, position=xyz))

        traj.append(_atoms)

    return traj


def combine_constraints(atoms, index_from_last=0, nats_mol=1, freeze_ratio=0.5):
    idx = np.argsort(atoms.positions[:, 2])[
        : int((len(atoms) - nats_mol) * freeze_ratio)
    ]
    fa = FixAtoms(indices=idx)
    fl = FixedLine(indices=len(atoms) - index_from_last - 1, direction=[0, 0, 1])
    atoms.set_constraint([fa, fl])

    return atoms


def merge_traj(atoms1, atoms2):
    atoms = atoms1.copy()
    to_attach = atoms2.copy()

    to_attach.positions += 2 * to_attach.cell[1]

    atoms += to_attach

    return atoms


def calculate(
    traj, generic_calculator, node_path, index_from_last=0, nats_mol=1, freeze_ratio=0.5
):
    results = []
    for image in tqdm(traj, desc="calculation progress"):
        _image = image.copy()
        _image = combine_constraints(
            _image,
            index_from_last=index_from_last,
            nats_mol=nats_mol,
            freeze_ratio=freeze_ratio,
        )
        calc = generic_calculator.get_calculator()
        _image.calc = calc

        dyn = BFGS(
            _image,
            trajectory=f"{node_path}/current_relax.traj",
            logfile=f"{node_path}/current_relax.log",
        )
        dyn.run(fmax=0.01, steps=200)

        _image.get_potential_energy()
        _image.get_forces()

        results.append(_image)

    return results


def pre_optimize(atoms, calc, path, relax_path, nats_mol=0, freeze_ratio=0.5):
    filename = f"{path}.traj"

    relax_name = f"{relax_path}_relaxation"
    if os.path.exists(filename):
        _atoms = read(filename)
    else:
        _atoms = atoms.copy()

    if freeze_ratio:
        idx = np.argsort(atoms.positions[:, 2])[
            : int((len(atoms) - nats_mol) * freeze_ratio)
        ]

        fa = FixAtoms(indices=idx)

        _atoms.set_constraint([fa])

    else:
        _atoms.set_constraint()

    _atoms = property_implemented(_atoms, calc)

    dyn = BFGS(_atoms, trajectory=f"{relax_name}.traj", logfile=f"{relax_name}.log")
    dyn.run(fmax=0.01, steps=200)

    _atoms.write(filename)

    return _atoms


def property_implemented(atoms, generic_calculator):
    calc = atoms.calc

    if (
        calc
        and not calc.calculation_required(atoms, ["energy"])
        and not calc.calculation_required(atoms, ["forces"])
    ):
        atoms.get_potential_energy()
        atoms.get_forces()
        print("calculator already implemented")

    else:
        try:
            calc = generic_calculator.get_calculator()
            print("got calculator from get_calculator() method")
        except Exception:
            calc = generic_calculator
            print("got calculator from generic_calculator")

        atoms.calc = calc
        atoms.get_potential_energy()
        atoms.get_forces()

    return atoms


def individual_run(
    traj,
    model,
    generic_calculator,
    node_path,
    basename,
    mol,
    freeze_ratio=0.5,
    index_from_last=0,
    nats_mol=1,
    el="",
):
    print(f"running for {model}  {el}")
    print(f"......{mol}")

    if os.path.exists(f"{node_path}/{mol}_{basename}_{model}_{el}.traj"):
        results = read(f"{node_path}/{mol}_{basename}_{model}_{el}.traj", index=":")

        for idx, atoms in enumerate(results):
            atoms = property_implemented(atoms, generic_calculator)
            results[idx] = atoms

    else:
        results = calculate(
            traj,
            generic_calculator,
            node_path,
            index_from_last=index_from_last,
            nats_mol=nats_mol,
            freeze_ratio=freeze_ratio,
        )

    write(f"{node_path}/{mol}_{basename}_{model}_{el}.traj", results)

    return results


def heatmap(model, Z, x1, x2, el, xrange, yrange):
    fig, ax = plt.subplots(figsize=(8, 6))

    heatmap = ax.imshow(
        Z,
        extent=(xrange[0], xrange[1], yrange[0], yrange[1]),
        origin="lower",
        cmap="viridis",
        alpha=0.7,
    )
    # sns.heatmap(Z, cmap='viridis', alpha=0.7, ax=ax)

    ax.scatter(x1, x2, s=100, edgecolor="black")
    texts = []

    for i, label in enumerate(el):
        sign = 0
        y_offset = -15
        if label in ["Ni", "Co"]:
            sign = 1

        if label in ["Rh", "Ir"]:
            sign = -1

        if label in ["Rh", "Ni"]:
            y_offset = 5

        if label == "Pt":
            y_offset = 0
            sign = 3

        text = ax.annotate(
            label,
            (x1[i], x2[i]),
            textcoords="offset points",
            xytext=(2.5 * sign, y_offset),
            ha="center",
            fontsize=10,
            color="black",
        )

        texts.append(text)

    ax.set_title(f"CO splitting on 211-surf - {model}")
    ax.set_xlabel("C* (eV)")
    ax.set_ylabel("O* (eV)")
    ax.set_xlim(xrange)
    ax.set_ylim(yrange)
    ax.grid(False)

    plt.colorbar(heatmap, ax=ax, label="barrier CO* + H* -> C*+OH* (eV)")
    plt.savefig(f"{model}_heatmap.png", dpi=300)


class COSplitting(zntrack.Node):
    """
    CO Splitting Node
    This node performs CO splitting analysis on the provided bulk structures.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of images to perform CO splitting analysis on.
    model : NodeWithCalculator
        Model node with calculator to perform CO splitting analysis.
    miller : list[int], default=[2,1,1]
        Miller index of the surface to be generated.
    supercell : list[int], default=[2,2,1]
        Supercell in a list format.
    layers : int, default=8
        Number of layers.
    vacuum : float, default=10.0
        Vacuum size in Angst.
    grid_step : float, default=0.3
        Step size of the grid for the placement of intermediates.
    freeze_ratio: float, default=0.5
        Ratio of bottom layers to be frozen for relaxations.
    frames_path : pathlib.Path
        Path to save frames.
    node_path : pathlib.Path
        Path to save additional information such as cache and heatmaps.

    Attributes
    ----------
    results : pd.DataFrame
        Results of CO splitting analysis.
    """

    data: list[ase.Atoms] = zntrack.deps()
    model: NodeWithCalculator = zntrack.deps()

    # adding more parameters
    miller: list[int] = zntrack.params(None)
    supercell: list[int] = zntrack.params(None)
    layers: int = zntrack.params(8)
    vacuum: float = zntrack.params(10.0)
    grid_step: float = zntrack.params(3.0)
    freeze_ratio: float = zntrack.params(0.5)
    node_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "outputs")
    frames_path: str = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    results: pd.DataFrame = zntrack.plots(y="dE", x="Formula")

    def run(self):  # noqa C901
        model = "model"

        if not self.miller:
            self.miller = [2, 1, 1]

        if not self.supercell:
            self.supercell = [2, 2, 1]

        # RPBE (C, O) referenced to CH4, H2O --> doi.org/10.1007/s11244-013-0169-0
        reference_data = {
            "Rh": [1.41, 0.21],
            "Cu": [3.53, 1.02],
            "Co": [1.70, -0.11],
            "Fe": [1.28, -0.8],
            "Ni": [1.53, 0.17],
            "Pt": [2.12, 1.30],
            "Ru": [1.26, -0.08],
            "Ir": [1.60, -0.08],
            "Pd": [1.53, 1.52],
            "Au": [4.75, 2.63],
            "Ag": [5.05, 1.90],
        }

        x1 = [reference_data[el][0] for el in reference_data]
        x2 = [reference_data[el][1] for el in reference_data]
        el = list(reference_data)

        # LSR obtained in doi.org/10.1007/s11244-013-0169-0
        def reaction(c, o):
            return 0.34 * c + 0.552 * o - 0.40

        def barrier_bep(reaction_step):
            return 1.12 * reaction_step + 1.20

        xrange = [-1.1, 6.1]
        yrange = [-1.1, 6.1]

        xgrid = np.linspace(xrange[0], xrange[1], 100)
        ygrid = np.linspace(yrange[0], yrange[1], 100)

        Xgrid, Ygrid = np.meshgrid(xgrid, ygrid)

        Zref = barrier_bep(reaction(Xgrid, Ygrid))

        heatmap_path = self.node_path / "heatmaps"
        cache_relaxations_path = self.node_path / "cached_relaxations"

        heatmap_path.mkdir(parents=True, exist_ok=True)
        cache_relaxations_path.mkdir(parents=True, exist_ok=True)

        heatmap(heatmap_path / "RPBE", Zref, x1, x2, el, xrange, yrange)

        mols = {}
        surfs = {}
        model_results = {}
        traj_dict = {}

        surfs[model] = {}
        mols[model] = {}

        mols[model]["CH4"] = pre_optimize(
            gas_phase("CH4", vacuum=self.vacuum),
            self.model.get_calculator(),
            self.node_path / f"{model}_CH4_gas",
            cache_relaxations_path / f"{model}_CH4_gas",
            freeze_ratio=0,
        ).get_potential_energy()

        mols[model]["H2O"] = pre_optimize(
            gas_phase("H2O", vacuum=self.vacuum),
            self.model.get_calculator(),
            self.node_path / f"{model}_H2O_gas",
            cache_relaxations_path / f"{model}_H2O_gas",
            freeze_ratio=0,
        ).get_potential_energy()

        mols[model]["H2"] = pre_optimize(
            gas_phase("H2", vacuum=self.vacuum),
            self.model.get_calculator(),
            self.node_path / f"{model}_H2_gas",
            cache_relaxations_path / f"{model}_H2_gas",
            freeze_ratio=0,
        ).get_potential_energy()

        for current_frame, bulk in tqdm(enumerate(self.data)):
            formula = bulk.get_chemical_formula(empirical=True)

            surf = gen_surf(
                bulk,
                miller=self.miller,
                layers=self.layers,
                vacuum=self.vacuum,
                supercell=self.supercell,
            )

            calc = self.model.get_calculator()
            surf = pre_optimize(
                surf,
                calc,
                self.node_path / f"{model}_{formula}_clean_surface",
                cache_relaxations_path / f"{model}_{formula}_clean_surface",
                freeze_ratio=self.freeze_ratio,
            )

            surfs[model][formula] = surf

        model_results[model] = {}
        traj_dict[model] = {}
        x1, x2, _formula, y = [], [], [], []
        for formula, surf in surfs[model].items():
            model_results[model][formula] = {}
            pos, _atoms = grid_placement(surf, atom="C", grid_step=self.grid_step)
            co_traj = gen_images(surf, pos, mol="CO")
            results = individual_run(
                co_traj,
                model,
                self.model,
                self.node_path,
                "",
                freeze_ratio=self.freeze_ratio,
                mol="CO",
                index_from_last=1,
                nats_mol=2,
                el=formula,
            )

            co_energies = [_image.get_potential_energy() for _image in results]
            np.min(co_energies)

            _co_bound_surf = results[np.argmin(co_energies)]
            _c_bound_surf = _co_bound_surf[:-1]

            c_bound_surf = relocate_atom(_c_bound_surf, idx=len(_c_bound_surf) - 1)
            _co_bound_surf = c_bound_surf + Atom(
                symbol="O", position=c_bound_surf[-1].position + (0, 0, 1.2)
            )

            co_bound_surf = pre_optimize(
                _co_bound_surf,
                self.model.get_calculator(),
                self.node_path / f"{model}_{formula}_CO_final",
                cache_relaxations_path / f"{model}_{formula}_CO_final",
                nats_mol=2,
                freeze_ratio=self.freeze_ratio,
            )

            co_bound_surf.get_potential_energy()

            _c_temp = co_bound_surf[:-1]
            _c_temp_2 = relocate_atom(_c_temp, idx=len(_c_temp) - 1)
            co_bound_surf = _c_temp_2 + Atom(
                symbol="O", position=_c_temp_2[-1].position + (0, 0, 1.2)
            )
            pos, _atoms = grid_placement(
                co_bound_surf, atom="H", grid_step=self.grid_step
            )
            h_traj = gen_images(co_bound_surf, pos, mol="H")
            results = individual_run(
                h_traj,
                model,
                self.model,
                self.node_path,
                "",
                freeze_ratio=self.freeze_ratio,
                mol="H",
                index_from_last=0,
                nats_mol=3,
                el=formula,
            )

            co_h_energies = [_image.get_potential_energy() for _image in results]

            _co_h_bound_surf = results[np.argmin(co_h_energies)]

            co_h_bound_surf = pre_optimize(
                _co_h_bound_surf,
                self.model.get_calculator(),
                self.node_path / f"{model}_{formula}_CO_H_final",
                cache_relaxations_path / f"{model}_{formula}_CO_H_final",
                nats_mol=3,
                freeze_ratio=self.freeze_ratio,
            )

            co_h_en = co_h_bound_surf.get_potential_energy()
            c_bound_surf = co_h_bound_surf[:-2]
            c_bound_surf = relocate_atom(c_bound_surf, idx=len(c_bound_surf) - 1)

            pos, _atoms = grid_placement(
                c_bound_surf, atom="O", grid_step=self.grid_step
            )
            oh_traj = gen_images(c_bound_surf, pos, mol="OH")
            results = individual_run(
                oh_traj,
                model,
                self.model,
                self.node_path,
                "",
                freeze_ratio=self.freeze_ratio,
                mol="OH",
                index_from_last=1,
                nats_mol=3,
                el=formula,
            )

            c_oh_energies = []
            for _image in results:
                distance = get_distances(
                    _image[-3].position, _image[-2].position, cell=_image.cell, pbc=True
                )[1][0][0]
                if distance > 2:
                    c_oh_energies.append(_image.get_potential_energy())
                else:
                    c_oh_energies.append(np.inf)

            _c_oh_bound_surf = results[np.argmin(c_oh_energies)]

            _c_o_temp = _c_oh_bound_surf[:-1]
            _c_o_temp_2 = relocate_atom(_c_o_temp, idx=len(_c_o_temp) - 1)
            _c_oh_bound_surf = _c_o_temp_2 + Atom(
                symbol="H", position=_c_o_temp_2[-1].position + (0, 0.8, 0.8)
            )

            c_oh_bound_surf = pre_optimize(
                _c_oh_bound_surf,
                self.model.get_calculator(),
                self.node_path / f"{model}_{formula}_C_OH_final",
                cache_relaxations_path / f"{model}_{formula}_C_OH_final",
                nats_mol=3,
                freeze_ratio=self.freeze_ratio,
            )

            to_append = merge_traj(co_h_bound_surf, c_oh_bound_surf)
            traj_dict[model][formula] = to_append

            c_oh_en = c_oh_bound_surf.get_potential_energy()

            distance = get_distances(
                c_oh_bound_surf[-3].position,
                c_oh_bound_surf[-2].position,
                cell=c_oh_bound_surf.cell,
                pbc=True,
            )[1][0][0]
            if distance > 2:
                bond_broken = True
            else:
                bond_broken = False

            pos, _atoms = grid_placement(surf, atom="C", grid_step=self.grid_step)
            c_traj = gen_images(surf, pos, mol="C")
            results = individual_run(
                c_traj,
                model,
                self.model,
                self.node_path,
                "",
                freeze_ratio=self.freeze_ratio,
                mol="C",
                index_from_last=0,
                nats_mol=1,
                el=formula,
            )

            _c_bound_surf = results[
                np.argmin([_image.get_potential_energy() for _image in results])
            ]
            _c_bound_surf = relocate_atom(_c_bound_surf, idx=len(_c_bound_surf) - 1)
            c_bound_surf = pre_optimize(
                _c_bound_surf,
                self.model.get_calculator(),
                self.node_path / f"{model}_{formula}_C_final",
                cache_relaxations_path / f"{model}_{formula}_C_final",
                nats_mol=1,
                freeze_ratio=self.freeze_ratio,
            )
            c_en = c_bound_surf.get_potential_energy()

            pos, _atoms = grid_placement(surf, atom="O", grid_step=self.grid_step)
            o_traj = gen_images(surf, pos, mol="O")
            results = individual_run(
                o_traj,
                model,
                self.model,
                self.node_path,
                "",
                freeze_ratio=self.freeze_ratio,
                mol="O",
                index_from_last=0,
                nats_mol=1,
                el=formula,
            )

            _o_bound_surf = results[
                np.argmin([_image.get_potential_energy() for _image in results])
            ]
            _o_bound_surf = relocate_atom(_o_bound_surf, idx=len(_o_bound_surf) - 1)
            o_bound_surf = pre_optimize(
                _o_bound_surf,
                self.model.get_calculator(),
                self.node_path / f"{model}_{formula}_O_final",
                cache_relaxations_path / f"{model}_{formula}_O_final",
                nats_mol=1,
                freeze_ratio=self.freeze_ratio,
            )
            o_en = o_bound_surf.get_potential_energy()

            model_results[model][formula]["CO*+H*->C*+OH*"] = float(c_oh_en - co_h_en)
            model_results[model][formula]["barrier(from bep rpbe)"] = float(
                barrier_bep(c_oh_en - co_h_en)
            )
            model_results[model][formula]["CH4->C*+2H2"] = float(
                c_en
                - (
                    surf.get_potential_energy()
                    + mols[model]["CH4"]
                    - 2 * mols[model]["H2"]
                )
            )
            model_results[model][formula]["H2O->O*+H2"] = float(
                o_en
                - (surf.get_potential_energy() + mols[model]["H2O"] - mols[model]["H2"])
            )
            model_results[model][formula]["bond_broken"] = bond_broken

            x1.append(
                c_en
                - (
                    surf.get_potential_energy()
                    + mols[model]["CH4"]
                    - 2 * mols[model]["H2"]
                )
            )
            x2.append(
                o_en
                - (surf.get_potential_energy() + mols[model]["H2O"] - mols[model]["H2"])
            )
            _formula.append(formula)
            y.append(c_oh_en - co_h_en)

        data = {"x1": x1, "x2": x2, "el": _formula, "y": y}

        df = pd.DataFrame(data)
        X = df[["x1", "x2"]]
        y = df["y"]

        LR = LinearRegression()

        LR.fit(X, y)

        y_pred = LR.predict(X)

        r_squared = float(r2_score(y, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y, y_pred)))

        m1 = float(LR.coef_[0])
        m2 = float(LR.coef_[1])
        b = float(LR.intercept_)

        model_results[model]["interpolation"] = {
            "formula": f"co_h->c_oh = {m1:.2f} * C + {m2:.2f} * O + {b:.2f}",
            "m1": m1,
            "m2": m2,
            "b": b,
            "r2": r_squared,
            "rmse": rmse,
        }

        def f(c, o):
            return m1 * c + m2 * o + b

        Z = barrier_bep(f(Xgrid, Ygrid))

        heatmap(heatmap_path / model, Z, x1, x2, _formula, xrange, yrange)

        with open(self.node_path / "full_data.json", "w") as json_file:
            json.dump(model_results, json_file, indent=4)

        results = []
        line = model_results[model]
        for el in line:
            if el != "interpolation":
                results.append(
                    {"Formula": el, "dE": model_results[model][el]["CO*+H*->C*+OH*"]}
                )
                ase.io.write(self.frames_path, traj_dict[model][el], append=True)

        self.results = pd.DataFrame(results)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))

    @property
    def figures(self) -> dict[str, go.Figure]:
        fig = px.line(self.results, x="Formula", y="dE", markers=True)
        fig.update_layout(
            title="Reaction Energy for H-assisted CO Splitting",
            xaxis_title="Formula",
            yaxis_title="dE (eV)",
        )
        fig.update_traces(customdata=np.stack([np.arange(len(self.results))], axis=-1))
        return {"ReactionEnergy": fig}

    @staticmethod
    def compare(*nodes: "COSplitting") -> ComparisonResults:
        frames = sum([node.frames for node in nodes], [])
        offset = 0
        fig = go.Figure()  # px.scatter()

        for i, node in enumerate(nodes):
            trajectory = node.data.copy()

            fig.add_trace(
                go.Bar(
                    x=node.results["Formula"],
                    y=node.results["dE"],
                    name=node.name,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=node.results["Formula"],
                    y=node.results["dE"],
                    mode="markers",
                    name=node.name,
                    marker={"color": "red"},
                    showlegend=False,
                    customdata=np.stack(
                        [np.arange(len(node.results["dE"])) + offset], axis=1
                    ),
                )
            )

            offset += len(node.results["dE"])

        results = []
        for atoms in trajectory:
            formula = atoms.get_chemical_formula(empirical=True)
            if "dE" in atoms.info:
                results.append({"Formula": formula, "dE": atoms.info["dE"]})

        if results:
            results = pd.DataFrame(results)
            fig.add_trace(
                go.Bar(
                    x=results["Formula"],
                    y=results["dE"],
                    name="reference",
                )
            )

        fig.update_layout(
            title="Comparison of Reaction Energies for H-assisted CO Splitting",
            xaxis_title="Formula",
            yaxis_title="dE (eV)",
            barmode="group",
            scattermode="group",
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

        return ComparisonResults(frames=frames, figures={"Reaction-Comparison": fig})
