import dataclasses

import ase
from ase.calculators.calculator import Calculator, all_changes


class _UpdateFramesCalc(Calculator):
    implemented_properties = ["energy", "forces"]

    def __init__(
        self, results_mapping: dict, info_mapping: dict, arrays_mapping: dict, **kwargs
    ):
        Calculator.__init__(self, **kwargs)
        self.results_mapping = results_mapping
        self.info_mapping = info_mapping
        self.arrays_mapping = arrays_mapping

    def calculate(
        self,
        atoms=ase.Atoms,
        properties=None,
        system_changes=all_changes,
    ):
        if properties is None:
            properties = self.implemented_properties
        Calculator.calculate(self, atoms, properties, system_changes)
        for target, key in self.results_mapping.items():
            if key is None:
                continue
            try:
                value = atoms.info[key]
            except KeyError:
                value = atoms.arrays[key]
            self.results[target] = value

        for target, key in self.info_mapping.items():
            # rename the key to target
            atoms.info[target] = atoms.info[key]
            del atoms.info[key]

        for target, key in self.arrays_mapping.items():
            # rename the key to target
            atoms.arrays[target] = atoms.arrays[key]
            del atoms.arrays[key]


# TODO: what if the energy is in the single point calculator but the forces are not?
@dataclasses.dataclass
class UpdateFramesCalc:
    results_mapping: dict[str, str] = dataclasses.field(default_factory=dict)
    info_mapping: dict[str, str] = dataclasses.field(default_factory=dict)
    arrays_mapping: dict[str, str] = dataclasses.field(default_factory=dict)

    def get_calculator(self, **kwargs) -> _UpdateFramesCalc:
        return _UpdateFramesCalc(
            results_mapping=self.results_mapping,
            info_mapping=self.info_mapping,
            arrays_mapping=self.arrays_mapping,
        )
