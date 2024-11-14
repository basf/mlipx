import pathlib

import ase.io
import zntrack


class Rattle(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
    stdev: float = zntrack.params(0.001)
    seed: int = zntrack.params(42)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        for atoms in self.data:
            atoms.rattle(stdev=self.stdev, seed=self.seed)
            ase.io.write(self.frames_path, atoms, append=True)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(ase.io.iread(f, format="extxyz"))
