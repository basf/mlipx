import dataclasses
import importlib
import typing as t
from pathlib import Path

import yaml
from ase.calculators.calculator import Calculator

from mlipx.abc import NodeWithCalculator
from mlipx.spec import MLIPSpec


class Device:
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"

    @staticmethod
    def resolve_auto() -> t.Literal["cpu", "cuda"]:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"


# TODO: add files as dependencies somehow!


@dataclasses.dataclass
class GenericASECalculator(NodeWithCalculator):
    """Generic ASE calculator.

    Load any ASE calculator from a module and class name.

    Parameters
    ----------
    module : str
        Module name containing the calculator class.
        For LJ this would be 'ase.calculators.lj'.
    class_name : str
        Class name of the calculator.
        For LJ this would be 'LennardJones'.
    kwargs : dict, default=None
        Additional keyword arguments to pass to the calculator.
        For LJ this could be {'epsilon': 1.0, 'sigma': 1.0}.
    device : str, default=None
        Device to use for the calculator.
        Can be 'auto', 'cpu', or 'cuda'.
        Utilizes the pytorch Device class to resolve
        the device automatically.

    """

    module: str
    class_name: str
    kwargs: dict[str, t.Any] | None = None
    device: t.Literal["auto", "cpu", "cuda"] | None = None
    spec: str | None = None

    def get_calculator(self, **kwargs) -> Calculator:
        if self.kwargs is not None:
            kwargs.update(self.kwargs)
        module = importlib.import_module(self.module)
        cls = getattr(module, self.class_name)
        if self.device is None:
            return cls(**kwargs)
        elif self.device == "auto":
            return cls(**kwargs, device=Device.resolve_auto())
        else:
            return cls(**kwargs, device=self.device)

    @property
    def available(self) -> bool:
        try:
            importlib.import_module(self.module)
            return True
        except ImportError:
            return False

    def get_spec(self) -> MLIPSpec | None:
        """
        Load mlips.yaml from <top_level_package>/spec/mlips.yaml
        """
        if self.spec is None:
            return None

        try:
            # Get top-level package name (before first dot)
            top_level_package = self.module.split(".")[0]
            package = importlib.import_module(top_level_package)
            base_path = Path(package.__path__[0])
            spec_path = base_path / "spec" / "mlips.yaml"
            with spec_path.open("r") as f:
                mlip_spec = yaml.safe_load(f)
            if self.spec is not None:
                spec_dict = mlip_spec.get(self.spec, None)
        except (ImportError, AttributeError, FileNotFoundError):
            # now try loading it from the mlipx package model spec
            package = importlib.import_module("mlipx")
            base_path = Path(package.__path__[0])
            spec_path = base_path / "spec" / "mlips.yaml"
            with spec_path.open("r") as f:
                mlip_spec = yaml.safe_load(f)
            if self.spec is not None:
                spec_dict = mlip_spec.get(self.spec, None)

        if isinstance(spec_dict, dict):
            # Ensure the spec is a dictionary
            spec_dict = MLIPSpec.model_validate(spec_dict)
        return spec_dict


if __name__ == "__main__":
    mlipx_dummy_calc = GenericASECalculator(
        module="mlipx.nodes",  # dummy path
        class_name="OrcaSinglePoint",  # dummy class
        spec="mace-mpa-0",  # this is what matters!
    )
    print(mlipx_dummy_calc.get_spec())
    # {'data': {'type': 'public_dataset', 'name': ['MPtrj', 'subsampled_Alexandria']}}
