import typing as t

import ase
import pandas as pd
import zntrack
from tqdm import tqdm, trange

from mlipx.abc import ASEKeys, NodeWithCalculator
from mlipx.utils import rmse


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

    plots: pd.DataFrame = zntrack.plots(
        y=["eform", "n_atoms"], independent=True, autosave=True
    )

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

        plots = []

        for atoms in self.data:
            chem = atoms.get_chemical_symbols()
            reference_energy = 0
            for element in chem:
                reference_energy += self.isolated_energies[element]
            E_form = atoms.get_potential_energy() - reference_energy
            self.formation_energy.append(E_form)
            plots.append({"eform": E_form, "n_atoms": len(atoms)})

        self.plots = pd.DataFrame(plots)

    @property
    def frames(self):
        for atom, energy in zip(self.data, self.formation_energy):
            atom.info[ASEKeys.formation_energy.value] = energy
        return self.data


class CompareFormationEnergy(zntrack.Node):
    data: CalculateFormationEnergy = zntrack.deps()
    reference: CalculateFormationEnergy = zntrack.deps()

    plots: pd.DataFrame = zntrack.plots(autosave=True)
    rmse: dict = zntrack.metrics()
    error: dict = zntrack.metrics()

    def run(self):
        eform_rmse = rmse(self.data.plots["eform"], self.reference.plots["eform"])
        # e_rmse = rmse(self.data.plots["energy"], self.reference.plots["energy"])
        self.rmse = {
            "eform": eform_rmse,
            "eform_per_atom": eform_rmse / len(self.data.plots),
        }

        all_plots = []

        for row_idx in trange(len(self.data.plots)):
            plots = {}
            plots["adjusted_eform_error"] = (
                self.data.plots["eform"].iloc[row_idx] - eform_rmse
            ) - self.reference.plots["eform"].iloc[row_idx]
            plots["adjusted_eform"] = (
                self.data.plots["eform"].iloc[row_idx] - eform_rmse
            )
            plots["adjusted_eform_error_per_atom"] = (
                plots["adjusted_eform_error"] / self.data.plots["n_atoms"].iloc[row_idx]
            )
            all_plots.append(plots)
        self.plots = pd.DataFrame(all_plots)

        # iterate over plots and save min/max
        self.error = {}
        for key in self.plots.columns:
            if "_error" in key:
                stripped_key = key.replace("_error", "")
                self.error[f"{stripped_key}_max"] = self.plots[key].max()
                self.error[f"{stripped_key}_min"] = self.plots[key].min()
