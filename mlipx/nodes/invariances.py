import pathlib

import ase
import ase.io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import tqdm
import zntrack

from mlipx.abc import ComparisonResults, NodeWithCalculator


class InvarianceNode(zntrack.Node):
    """Base class for testing invariances."""

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)
    n_points: int = zntrack.params(50)

    metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots()

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        """Common logic for invariance testing."""
        atoms = self.data[self.data_id]
        calc = self.model.get_calculator()
        atoms.calc = calc

        rng = np.random.default_rng()
        energies = []
        for _ in tqdm.tqdm(range(self.n_points)):
            self.apply_transformation(atoms, rng)
            energies.append(atoms.get_potential_energy())
            ase.io.write(self.frames_path, atoms, append=True)

        self.plots = pd.DataFrame(energies, columns=["energy"])

        self.metrics = {
            "mean": float(np.mean(energies)),
            "std": float(np.std(energies)),
        }

    @property
    def frames(self):
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, ":"))

    def apply_transformation(self, atoms_copy: ase.Atoms, rng: np.random.Generator):
        """To be implemented by child classes."""
        raise NotImplementedError("Subclasses must implement apply_transformation()")

    @staticmethod
    def compare(*nodes: "InvarianceNode") -> ComparisonResults:
        if len(nodes) == 0:
            raise ValueError("No nodes to compare")

        fig = go.Figure()
        for node in nodes:
            fig.add_trace(
                go.Scatter(
                    x=np.arange(node.n_points),
                    y=node.plots["energy"] - node.metrics["mean"],
                    mode="markers",
                    name=node.name.replace(f"_{node.__class__.__name__}", ""),
                )
            )

        fig.update_layout(
            title=f"Energy vs step ({nodes[0].__class__.__name__})",
            xaxis_title="Steps",
            yaxis_title="Adjusted energy",
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
            frames=nodes[0].frames, figures={"energy_vs_steps_adjusted": fig}
        )


class TranslationalInvariance(InvarianceNode):
    """Test translational invariance by random box translocation."""

    def apply_transformation(self, atoms_copy: ase.Atoms, rng: np.random.Generator):
        translation = rng.uniform(-1, 1, 3)
        atoms_copy.positions += translation


class RotationalInvariance(InvarianceNode):
    """Test rotational invariance by random rotation of the box."""

    def apply_transformation(self, atoms_copy: ase.Atoms, rng: np.random.Generator):
        angle = rng.uniform(-90, 90)
        direction = rng.choice(["x", "y", "z"])
        atoms_copy.rotate(angle, direction, rotate_cell=any(atoms_copy.pbc))


class PermutationInvariance(InvarianceNode):
    """Test permutation invariance by permutation of atoms of the same species."""

    def apply_transformation(self, atoms_copy: ase.Atoms, rng: np.random.Generator):
        species = np.unique(atoms_copy.get_chemical_symbols())
        for s in species:
            indices = np.where(atoms_copy.get_chemical_symbols() == s)[0]
            rng.shuffle(indices)
            atoms_copy.positions[indices] = rng.permutation(
                atoms_copy.positions[indices], axis=0
            )
