import ase
import numpy as np
import tqdm
import zntrack

from mlipx.abc import NodeWithCalculator


class TranslationalInvariance(zntrack.Node):
    """Test translational invariance by random box translocation.

    Parameters
    ----------
    model : NodeWithCalculator
        Node providing the calculator object to evaluate.
    data : list[ase.Atoms]
        List of ASE atoms objects to evaluate.
    data_id : int, default=-1
        Index of the atoms object to evaluate.
    n_points : int, default=50
        Number of random translations to evaluate.

    Attributes
    ----------
    metrics : dict
        Dictionary with the mean and standard deviation of the energy.
        For a translational invariance, the standard deviation should zero.

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)
    n_points: int = zntrack.params(50)

    metrics: dict = zntrack.metrics()

    def run(self):
        atoms = self.data[self.data_id]
        calc = self.model.get_calculator()

        rng = np.random.default_rng()
        energies = []
        for _ in tqdm.tqdm(range(self.n_points)):
            translation = rng.uniform(-1, 1, 3)
            atoms_copy = atoms.copy()
            atoms_copy.positions += translation
            energies.append(calc.get_potential_energy(atoms_copy))

        self.metrics = {
            "mean": np.mean(energies),
            "std": np.std(energies),
        }


class RotationalInvariance(zntrack.Node):
    """Test rotational invariance by random rotation of the box.

    Parameters
    ----------
    model : NodeWithCalculator
        Node providing the calculator object to evaluate.
    data : list[ase.Atoms]
        List of ASE atoms objects to evaluate.
    data_id : int, default=-1
        Index of the atoms object to evaluate.
    n_points : int, default=50
        Number of random rotations to evaluate.

    Attributes
    ----------
    metrics : dict
        Dictionary with the mean and standard deviation of the energy.
        For a rotational invariance, the standard deviation should zero.

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)
    n_points: int = zntrack.params(50)

    metrics: dict = zntrack.metrics()

    def run(self):
        atoms = self.data[self.data_id]
        calc = self.model.get_calculator()

        rng = np.random.default_rng()
        energies = []
        for _ in tqdm.tqdm(range(self.n_points)):
            atoms_copy = atoms.copy()
            angle = rng.uniform(-90, 90)
            direction = rng.choice(["x", "y", "z"])
            atoms_copy.rotate(angle, direction, rotate_cell=any(atoms_copy.pbc))
            energies.append(calc.get_potential_energy(atoms_copy))

        self.metrics = {
            "mean": np.mean(energies),
            "std": np.std(energies),
        }


class PermutationInvariance(zntrack.Node):
    """Test permutation invariance by random permutation of atoms of the same species.

    Parameters
    ----------
    model : NodeWithCalculator
        Node providing the calculator object to evaluate.
    data : list[ase.Atoms]
        List of ASE atoms objects to evaluate.
    data_id : int, default=-1
        Index of the atoms object to evaluate.
    n_points : int, default=50
        Number of random permutations to evaluate.

    Attributes
    ----------
    metrics : dict
        Dictionary with the mean and standard deviation of the energy.
        For a permutation invariance, the standard deviation should zero.

    """

    model: NodeWithCalculator = zntrack.deps()
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)
    n_points: int = zntrack.params(50)

    metrics: dict = zntrack.metrics()

    def run(self):
        atoms = self.data[self.data_id]
        calc = self.model.get_calculator()

        rng = np.random.default_rng()
        energies = []
        for _ in tqdm.tqdm(range(self.n_points)):
            atoms_copy = atoms.copy()
            species = np.unique(atoms_copy.get_chemical_symbols())
            for s in species:
                indices = np.where(atoms_copy.get_chemical_symbols() == s)[0]
                rng.shuffle(indices)
                atoms_copy.positions[indices] = rng.permutation(
                    atoms_copy.positions[indices], axis=0
                )
            energies.append(calc.get_potential_energy(atoms_copy))

        self.metrics = {
            "mean": np.mean(energies),
            "std": np.std(energies),
        }
