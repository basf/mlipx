import pathlib
import typing as t
from enum import Enum

import ase.io
import numpy as np
import tqdm
import zntrack


class FilteringType(str, Enum):
    """
    Enum defining types of filtering to apply on atomic configurations.

    Attributes
    ----------
    COMBINATIONS : str
        Filters to include atoms with elements that are any
        subset of the specified elements.
    EXCLUSIVE : str
        Filters to include atoms that contain *only* the specified elements.
    INCLUSIVE : str
        Filters to include atoms that contain *at least* the specified elements.
    """

    COMBINATIONS = "combinations"
    EXCLUSIVE = "exclusive"
    INCLUSIVE = "inclusive"


def filter_atoms(
    atoms: ase.Atoms,
    element_subset: list[str],
    filtering_type: t.Optional[FilteringType] = None,
) -> bool:
    """
    Filters an atomic configuration based on the
    specified filtering type and element subset.

    Parameters
    ----------
    atoms : ase.Atoms
        Atomic configuration to filter.
    element_subset : list[str]
        List of elements to be considered during filtering.
    filtering_type : FilteringType, optional
        Type of filtering to apply (COMBINATIONS, EXCLUSIVE, or INCLUSIVE).
        If None, all atoms pass the filter.

    Returns
    -------
    bool
        True if the atomic configuration passes the filter, False otherwise.

    References
    ----------
    Adapted from github.com/ACEsuit/mace

    Raises
    ------
    ValueError
        If the provided filtering_type is not recognized.
    """
    if filtering_type is None:
        return True
    elif filtering_type == FilteringType.COMBINATIONS:
        atom_symbols = np.unique(atoms.symbols)
        return all(x in element_subset for x in atom_symbols)
    elif filtering_type == FilteringType.EXCLUSIVE:
        atom_symbols = set(atoms.symbols)
        return atom_symbols == set(element_subset)
    elif filtering_type == FilteringType.INCLUSIVE:
        atom_symbols = np.unique(atoms.symbols)
        return all(x in atom_symbols for x in element_subset)
    else:
        raise ValueError(
            f"Filtering type {filtering_type} not recognized."
            " Must be one of 'none', 'exclusive', or 'inclusive'."
        )


class FilterAtoms(zntrack.Node):
    """
    ZnTrack node that filters a list of atomic configurations
     based on specified elements and filtering type.

    Attributes
    ----------
    data : list[ase.Atoms]
        List of atomic configurations to filter.
    elements : list[str]
        List of elements to use as the filtering subset.
    filtering_type : FilteringType
        Type of filtering to apply (INCLUSIVE, EXCLUSIVE, or COMBINATIONS).
    frames_path : pathlib.Path
        Path to store filtered atomic configuration frames.

    Methods
    -------
    run()
        Filters atomic configurations and writes the results to `frames_path`.
    frames() -> list[ase.Atoms]
        Loads filtered atomic configurations from `frames_path`.
    """

    data: list[ase.Atoms] = zntrack.deps()
    elements: list[str] = zntrack.params()
    filtering_type: FilteringType = zntrack.params(FilteringType.INCLUSIVE.value)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        """
        Applies filtering to atomic configurations in
        `data` and saves the results to `frames_path`.
        """
        for atoms in tqdm.tqdm(self.data):
            if filter_atoms(atoms, self.elements, self.filtering_type):
                ase.io.write(self.frames_path, atoms, append=True)

    @property
    def frames(self) -> list[ase.Atoms]:
        """Loads the filtered atomic configurations from the `frames_path` file.

        Returns
        -------
        list[ase.Atoms]
            List of filtered atomic configuration frames.
        """
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))
