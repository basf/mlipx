"""Abstract base classes and type hints."""

import typing as t
from enum import Enum

import ase
import plotly.graph_objects as go
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
