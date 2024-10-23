import ase
import zntrack

from mlipx.abc import ASEKeys


class CalculateFormationEnergy(zntrack.Node):
    """
    Calculate formation energy.

    Parameters
    ----------
    data : list[ase.Atoms]
        ASE atoms object with appropriate tags in info
    """

    data: list[ase.Atoms] = zntrack.deps()

    formation_energy: list = zntrack.outs(independent=True)

    def run(self):
        self.formation_energy = []
        for atom in self.data:
            chem = atom.get_chemical_symbols()
            reference_energy = 0
            for element in chem:
                reference_energy += atom.info[ASEKeys.isolated_energies.value][element]
            E_form = atom.get_potential_energy() - reference_energy
            self.formation_energy.append(E_form)

    @property
    def frames(self):
        for atom, energy in zip(self.data, self.formation_energy):
            atom.info[ASEKeys.formation_energy.value] = energy
        return self.data
