import typing as t

import ase
import zntrack
from tqdm import tqdm

from mlipx.abc import ASEKeys, NodeWithCalculator


class CalculateFormationEnergy(zntrack.Node):
    """
    Calculate formation energy.

    Parameters
    ----------
    data : list[ase.Atoms]
        ASE atoms object with appropriate tags in info
    """

    data: list[ase.Atoms] = zntrack.deps()
    model: t.Optional[NodeWithCalculator] = zntrack.deps(None)

    formation_energy: list = zntrack.outs(independent=True)
    isolated_energies: dict = zntrack.outs(independent=True)

    def get_isolated_energies(self) -> dict[str, float]:
        # get all unique elements
        isolated_energies = {}
        for atoms in tqdm(self.data, desc="Getting isolated energies"):
            for element in set(atoms.get_chemical_symbols()):
                if self.model is None:
                    if element not in isolated_energies:
                        isolated_energies[element] = atoms.info[
                            ASEKeys.isolated_energies.value
                        ][element]
                    else:
                        assert (
                            isolated_energies[element]
                            == atoms.info[ASEKeys.isolated_energies.value][element]
                        )
                else:
                    if element not in isolated_energies:
                        box = ase.Atoms(
                            element,
                            positions=[[50, 50, 50]],
                            cell=[100, 100, 100],
                            pbc=True,
                        )
                        box.calc = self.model.get_calculator()
                        isolated_energies[element] = box.get_potential_energy()

        return isolated_energies

    def run(self):
        self.formation_energy = []
        self.isolated_energies = self.get_isolated_energies()

        for atom in self.data:
            chem = atom.get_chemical_symbols()
            reference_energy = 0
            for element in chem:
                reference_energy += self.isolated_energies[element]
            E_form = atom.get_potential_energy() - reference_energy
            self.formation_energy.append(E_form)

    @property
    def frames(self):
        for atom, energy in zip(self.data, self.formation_energy):
            atom.info[ASEKeys.formation_energy.value] = energy
        return self.data
