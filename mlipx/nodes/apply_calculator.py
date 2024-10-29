import pathlib

import ase
import h5py
import tqdm
import znh5md
import zntrack
from ase.calculators.calculator import all_properties

from mlipx.abc import NodeWithCalculator
from mlipx.utils import freeze_copy_atoms


class ApplyCalculator(zntrack.Node):
    """
    Apply a calculator to a list of atoms objects and store the results in a H5MD file.

    Parameters
    ----------
    data : list[ase.Atoms]
        List of atoms objects to calculate.
    model : NodeWithCalculator, optional
        Node providing the calculator object to apply to the data.
    """

    data: list[ase.Atoms] = zntrack.deps()
    model: NodeWithCalculator | None = zntrack.deps()

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.h5")

    def run(self):
        frames = []
        if self.model is not None:
            calc = self.model.get_calculator()

            # Some calculators, e.g. MACE do not follow the ASE API correctly.
            #  and we need to fix some keys in `all_properties`
            all_properties.append("node_energy")

            for atoms in tqdm.tqdm(self.data):
                atoms.calc = calc
                atoms.get_potential_energy()
                frames.append(freeze_copy_atoms(atoms))
        else:
            frames = self.data

        io = znh5md.IO(self.frames_path)
        io.extend(frames)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "rb") as f:
            with h5py.File(f) as file:
                return list(znh5md.IO(file_handle=file))
