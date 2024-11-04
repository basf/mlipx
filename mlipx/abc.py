"""Abstract base classes and type hints."""

import abc
import dataclasses
import pathlib
import typing as t
from enum import Enum

import ase
import h5py
import plotly.graph_objects as go
import znh5md
import zntrack
from ase.calculators.calculator import Calculator
from ase.md.md import MolecularDynamics

T = t.TypeVar("T", bound=zntrack.Node)


class Optimizer(str, Enum):
    FIRE = "FIRE"
    BFGS = "BFGS"
    LBFGS = "LBFGS"


class ASEKeys(str, Enum):
    formation_energy = "formation_energy"
    isolated_energies = "isolated_energies"


class NodeWithCalculator(t.Protocol[T]):
    def get_calculator(self, **kwargs) -> Calculator: ...


class NodeWithMolecularDynamics(t.Protocol[T]):
    def get_molecular_dynamics(self, atoms: ase.Atoms) -> MolecularDynamics: ...


FIGURES = t.Dict[str, go.Figure]
FRAMES = t.List[ase.Atoms]


class ComparisonResults(t.TypedDict):
    frames: FRAMES
    figures: FIGURES


@dataclasses.dataclass
class DynamicsObserver:
    @property
    def name(self) -> str:
        return self.__class__.__name__

    def initialize(self, atoms: ase.Atoms) -> None:
        pass

    @abc.abstractmethod
    def check(self, atoms: ase.Atoms) -> bool: ...


@dataclasses.dataclass
class DynamicsModifier:
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abc.abstractmethod
    def modify(self, thermostat, step, total_steps) -> None: ...


class ProcessAtoms(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
    data_id: int = zntrack.params(-1)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.h5")

    @property
    def frames(self) -> FRAMES:
        with self.state.fs.open(self.frames_path, "r") as f:
            with h5py.File(f, "r") as h5f:
                return znh5md.IO(file_handle=h5f)[:]


class ProcessFrames(zntrack.Node):
    data: list[ase.Atoms] = zntrack.deps()
