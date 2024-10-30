import pathlib

import ase
import ase.io as aio
import zntrack


class Smiles2Conformers(zntrack.Node):
    """Create conformers from a SMILES string.

    Parameters
    ----------
    smiles : str
        The SMILES string.
    num_confs : int
        The number of conformers to generate.
    random_seed : int
        The random seed.
    max_attempts : int
        The maximum number of attempts.
    """

    smiles: str = zntrack.params()
    num_confs: int = zntrack.params()
    random_seed: int = zntrack.params(42)
    max_attempts: int = zntrack.params(1000)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        from rdkit2ase import smiles2conformers

        conformers = smiles2conformers(
            self.smiles,
            numConfs=self.num_confs,
            randomSeed=self.random_seed,
            maxAttempts=self.max_attempts,
        )
        aio.write(self.frames_path, conformers)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(aio.iread(f, format="extxyz"))


class BuildBox(zntrack.Node):
    """Build a box from a list of atoms.

    Parameters
    ----------
    data : list[list[ase.Atoms]]
        A list of lists of ASE Atoms objects representing
        the molecules to be packed.
    counts : list[int]
        A list of integers representing the number of each
        type of molecule.
    density : float
        The target density of the packed system in kg/m^3

    """

    data: list[list[ase.Atoms]] = zntrack.deps()
    counts: list[int] = zntrack.params()
    density: float = zntrack.params(1000)
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        from rdkit2ase import pack

        atoms = pack(data=self.data, counts=self.counts, density=self.density)
        aio.write(self.frames_path, atoms)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(aio.iread(f, format="extxyz"))
