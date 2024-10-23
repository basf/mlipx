import pandas as pd
import tqdm
import zntrack

from mlipx.abc import ComparisonResults
from mlipx.nodes.evaluate_calculator import EvaluateCalculatorResults, get_figure
from mlipx.utils import rmse, shallow_copy_atoms


class CompareCalculatorResults(zntrack.Node):
    data: EvaluateCalculatorResults = zntrack.deps()
    reference: EvaluateCalculatorResults = zntrack.deps()

    plots: pd.DataFrame = zntrack.plots(autosave=True)
    rmse: dict = zntrack.metrics()
    error: dict = zntrack.metrics()

    def run(self):
        eform_rmse = rmse(self.data.plots["eform"], self.reference.plots["eform"])
        e_rmse = rmse(self.data.plots["energy"], self.reference.plots["energy"])
        self.rmse = {
            "eform": eform_rmse,
            "energy": e_rmse,
            "eform_per_atom": eform_rmse / len(self.data.plots),
            "energy_per_atom": e_rmse / len(self.data.plots),
            "fmax": rmse(self.data.plots["fmax"], self.reference.plots["fmax"]),
            "fnorm": rmse(self.data.plots["fnorm"], self.reference.plots["fnorm"]),
        }

        self.plots = pd.DataFrame()

        for row_idx in tqdm.trange(len(self.data.plots)):
            plots = {}
            plots["adjusted_eform_error"] = (
                self.data.plots["eform"].iloc[row_idx] - eform_rmse
            ) - self.reference.plots["eform"].iloc[row_idx]
            plots["adjusted_energy_error"] = (
                self.data.plots["energy"].iloc[row_idx] - e_rmse
            ) - self.reference.plots["energy"].iloc[row_idx]
            plots["adjusted_eform"] = (
                self.data.plots["eform"].iloc[row_idx] - eform_rmse
            )
            plots["adjusted_energy"] = self.data.plots["energy"].iloc[row_idx] - e_rmse

            plots["adjusted_eform_error_per_atom"] = (
                plots["adjusted_eform_error"] / self.data.plots["n_atoms"].iloc[row_idx]
            )
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

            self.plots = self.plots.append(plots, ignore_index=True)

        # iterate over plots and save min/max
        self.error = {}
        for key in self.plots.columns:
            if "_error" in key:
                stripped_key = key.replace("_error", "")
                self.error[f"{stripped_key}_max"] = self.plots[key].max()
                self.error[f"{stripped_key}_min"] = self.plots[key].min()

    @property
    def frames(self):
        return self.data.frames

    def compare(self, *nodes: "CompareCalculatorResults") -> ComparisonResults:
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

        return {
            "frames": frames,
            "figures": figures,
        }
