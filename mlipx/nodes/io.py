import pathlib
import typing as t

import ase.io
import h5py
import znh5md
import zntrack


class LoadDataFile(zntrack.Node):
    """Load a trajectory file.

    Entry point of trajectory data for the use in other nodes.

    Parameters
    ----------
    path : str | pathlib.Path
        Path to the trajectory file.
    start : int, default=0
        Index of the first frame to load.
    stop : int, default=None
        Index of the last frame to load.
    step : int, default=1
        Step size between frames.

    Attributes
    ----------
    frames : list[ase.Atoms]
        Loaded frames.
    """

    path: str | pathlib.Path = zntrack.deps_path()
    # TODO these are not used
    start: int = zntrack.params(0)
    stop: t.Optional[int] = zntrack.params(None)
    step: int = zntrack.params(1)

    def run(self):
        pass

    @property
    def frames(self) -> list[ase.Atoms]:
        if pathlib.Path(self.path).suffix in [".h5", ".h5md"]:
            with self.state.fs.open(self.path, "rb") as f:
                with h5py.File(f) as file:
                    return znh5md.IO(file_handle=file)[
                        self.start : self.stop : self.step
                    ]
        else:
            format = pathlib.Path(self.path).suffix.lstrip(".")
            if format == "xyz":
                format = "extxyz"  # force ase to use the extxyz reader
            with self.state.fs.open(self.path, "r") as f:
                return list(
                    ase.io.iread(
                        f, format=format, index=slice(self.start, self.stop, self.step)
                    )
                )
