import pathlib

import ase.io
import zntrack
from mp_api import client
from pymatgen.io.ase import AseAtomsAdaptor


class MPRester(zntrack.Node):
    """Search the materials project database.

    Parameters
    ----------
    search_kwargs: dict
        The search parameters for the materials project database.

    Example
    -------
    >>> os.environ["MP_API_KEY"] = "your_api_key"
    >>> MPRester(search_kwargs={"material_ids": ["mp-1234"]})

    """

    search_kwargs: dict = zntrack.params()
    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        with client.MPRester() as mpr:
            docs = mpr.materials.search(**self.search_kwargs)

        frames = []
        adaptor = AseAtomsAdaptor()

        for entry in docs:
            structure = entry.structure
            atoms = adaptor.get_atoms(structure)
            frames.append(atoms)

        ase.io.write(self.frames_path, frames)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, mode="r") as f:
            return list(ase.io.iread(f, format="extxyz"))
