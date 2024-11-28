import contextlib

import pandas as pd
import tqdm
import zntrack
from ase.calculators.calculator import PropertyNotImplementedError

from mlipx.abc import FIGURES, FRAMES, ComparisonResults
from mlipx.nodes.evaluate_calculator import EvaluateCalculatorResults, get_figure
from mlipx.utils import rmse, shallow_copy_atoms


class CompareCalculatorResults(zntrack.Node):
    """
    CompareCalculatorResults is a node that compares the results of two calculators.
    It calculates the RMSE between the two calculators and adjusts plots accordingly.
    It calculates the error between the two calculators and saves the min/max values.

    Parameters
    ----------
    data : EvaluateCalculatorResults
            The results of the first calculator.
    reference : EvaluateCalculatorResults
        The results of the second calculator.
        The results of the first calculator will be compared to these results.
    """

    data: EvaluateCalculatorResults = zntrack.deps()
    reference: EvaluateCalculatorResults = zntrack.deps()

    plots: pd.DataFrame = zntrack.plots(autosave=True)
    rmse: dict = zntrack.metrics()
    error: dict = zntrack.metrics()

    def run(self):
        e_rmse = rmse(self.data.plots["energy"], self.reference.plots["energy"])
        self.rmse = {
            "energy": e_rmse,
            "energy_per_atom": e_rmse / len(self.data.plots),
            "fmax": rmse(self.data.plots["fmax"], self.reference.plots["fmax"]),
            "fnorm": rmse(self.data.plots["fnorm"], self.reference.plots["fnorm"]),
        }

        all_plots = []

        for row_idx in tqdm.trange(len(self.data.plots)):
            plots = {}
            plots["adjusted_energy_error"] = (
                self.data.plots["energy"].iloc[row_idx] - e_rmse
            ) - self.reference.plots["energy"].iloc[row_idx]
            plots["adjusted_energy"] = self.data.plots["energy"].iloc[row_idx] - e_rmse
            plots["adjusted_energy_error_per_atom"] = (
                plots["adjusted_energy_error"]
                / self.data.plots["n_atoms"].iloc[row_idx]
            )

            plots["fmax_error"] = (
                self.data.plots["fmax"].iloc[row_idx]
                - self.reference.plots["fmax"].iloc[row_idx]
            )
            plots["fnorm_error"] = (
                self.data.plots["fnorm"].iloc[row_idx]
                - self.reference.plots["fnorm"].iloc[row_idx]
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

    @property
    def frames(self) -> FRAMES:
        return self.data.frames

    @property
    def figures(self) -> FIGURES:
        figures = {}
        for key in self.plots.columns:
            figures[key] = get_figure(key, [self])
        return figures

    def compare(self, *nodes: "CompareCalculatorResults") -> ComparisonResults:  # noqa C901
        if len(nodes) == 0:
            raise ValueError("No nodes to compare provided")
        figures = {}
        frames_info = {}
        for key in nodes[0].plots.columns:
            if not all(key in node.plots.columns for node in nodes):
                raise ValueError(f"Key {key} not found in all nodes")
            # check frames are the same
            figures[key] = get_figure(key, nodes)

        for node in nodes:
            for key in node.plots.columns:
                frames_info[f"{node.name}_{key}"] = node.plots[key].values

            # TODO: calculate the rmse difference between a fixed
            # one and all the others and shift them accordingly
            # and plot as energy_shifted

            # plot error between curves
            # mlipx pass additional flags to compare function
            # have different compare methods also for correlation plots

        frames = [shallow_copy_atoms(x) for x in nodes[0].frames]
        for key, values in frames_info.items():
            for atoms, value in zip(frames, values):
                atoms.info[key] = value

        for node in nodes:
            for node_atoms, atoms in zip(node.frames, frames):
                if len(node_atoms) != len(atoms):
                    raise ValueError("Atoms objects have different lengths")
                with contextlib.suppress(RuntimeError, PropertyNotImplementedError):
                    atoms.info[f"{node.name}_energy"] = (
                        node_atoms.get_potential_energy()
                    )
                    atoms.arrays[f"{node.name}_forces"] = node_atoms.get_forces()

        for ref_atoms, atoms in zip(nodes[0].reference.frames, frames):
            with contextlib.suppress(RuntimeError, PropertyNotImplementedError):
                atoms.info["ref_energy"] = ref_atoms.get_potential_energy()
                atoms.arrays["ref_forces"] = ref_atoms.get_forces()

        return {
            "frames": frames,
            "figures": figures,
        }
