import fnmatch
import os

import plotly.graph_objects as go
import plotly.io as pio
import zntrack
from dvc.api import DVCFileSystem


def show(file: str) -> None:
    pio.renderers.default = "sphinx_gallery"

    figure = pio.read_json(f"source/figures/{file}")
    figure.update_layout(
        {
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
        }
    )
    figure.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="rgba(120, 120, 120, 0.3)", zeroline=False
    )
    figure.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="rgba(120, 120, 120, 0.3)", zeroline=False
    )
    figure.show()


def get_plots(name: str, url: str) -> dict[str, go.Figure]:
    os.chdir(url)
    pio.renderers.default = "sphinx_gallery"

    fs = DVCFileSystem(subrepos=True)

    all_nodes = [x.addressing for x in fs.repo.stage.collect()]
    filtered_nodes = [x for x in all_nodes if fnmatch.fnmatch(x, name)]

    node_instances = {}
    for node_name in filtered_nodes:
        node_instances[node_name] = zntrack.from_rev(node_name, fs=fs)

    result = node_instances[filtered_nodes[0]].compare(*node_instances.values())
    return result["figures"]
