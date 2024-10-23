import ase
import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator


def freeze_copy_atoms(atoms: ase.Atoms) -> ase.Atoms:
    atoms_copy = atoms.copy()
    if atoms.calc is not None:
        atoms_copy.calc = SinglePointCalculator(atoms_copy)
        atoms_copy.calc.results = atoms.calc.results
    return atoms_copy


def shallow_copy_atoms(atoms: ase.Atoms) -> ase.Atoms:
    """Create a shallow copy of an ASE atoms object."""
    atoms_copy = ase.Atoms(
        positions=atoms.positions,
        numbers=atoms.numbers,
        cell=atoms.cell,
        pbc=atoms.pbc,
    )
    return atoms_copy


def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred) ** 2))
