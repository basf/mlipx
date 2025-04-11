import fnmatch
import importlib.metadata
import json
import pathlib
import sys
import uuid
import webbrowser

import dvc.api
import plotly.io as pio
import typer
import zntrack
from rich import box
from rich.console import Console
from rich.table import Table
from tqdm import tqdm
from typing_extensions import Annotated
from zndraw import ZnDraw

from mlipx import benchmark, recipes

app = typer.Typer()
app.add_typer(recipes.app, name="recipes")
app.add_typer(benchmark.app, name="benchmark")

# Load plugins

entry_points = importlib.metadata.entry_points(group="mlipx.recipes")
for entry_point in entry_points:
    entry_point.load()


@app.command()
def main():
    typer.echo("Hello World")


@app.command()
def info():
    """Print the version of mlipx and the available models."""
    from mlipx.models import AVAILABLE_MODELS  # slow import

    console = Console()
    # Get Python environment info
    python_version = sys.version.split()[0]
    python_executable = sys.executable
    python_platform = sys.platform

    py_table = Table(title="🐍 Python Environment", box=box.ROUNDED)
    py_table.add_column("Version", style="cyan", no_wrap=True)
    py_table.add_column("Executable", style="magenta")
    py_table.add_column("Platform", style="green")
    py_table.add_row(python_version, python_executable, python_platform)

    # Get model availability
    mlip_table = Table(title="🧠 MLIP Codes", box=box.ROUNDED)
    mlip_table.add_column("Model", style="bold")
    mlip_table.add_column("Available", style="bold")

    for model in sorted(AVAILABLE_MODELS):
        status = AVAILABLE_MODELS[model]
        if status is True:
            mlip_table.add_row(model, "[green]:heavy_check_mark: Yes[/green]")
        elif status is False:
            mlip_table.add_row(model, "[red]:x: No[/red]")
        elif status is None:
            mlip_table.add_row(model, "[yellow]:warning: Unknown[/yellow]")
        else:
            mlip_table.add_row(model, "[red]:boom: Error[/red]")

    # Get versions of key packages
    mlipx_table = Table(title="📦 mlipx Ecosystem", box=box.ROUNDED)
    mlipx_table.add_column("Package", style="bold")
    mlipx_table.add_column("Version", style="cyan")

    for package in ["mlipx", "zntrack", "zndraw"]:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "[red]Not installed[/red]"
        mlipx_table.add_row(package, version)

    # Display all
    console.print(mlipx_table)
    console.print(py_table)
    console.print(mlip_table)


@app.command()
def compare(  # noqa C901
    nodes: Annotated[list[str], typer.Argument(help="Path to the node to compare")],
    zndraw_url: Annotated[
        str,
        typer.Option(
            envvar="ZNDRAW_URL",
            help="URL of the ZnDraw server to visualize the results",
        ),
    ],
    kwarg: Annotated[list[str], typer.Option("--kwarg", "-k")] = None,
    token: Annotated[str, typer.Option("--token")] = None,
    glob: Annotated[
        bool, typer.Option("--glob", help="Allow glob patterns to select nodes.")
    ] = False,
    convert_nan: Annotated[bool, typer.Option()] = False,
    browser: Annotated[
        bool,
        typer.Option(
            help="""Whether to open the ZnDraw GUI in the default web browser."""
        ),
    ] = True,
    figures_path: Annotated[
        str | None,
        typer.Option(
            help="Provide a path to save the figures to."
            "No figures will be saved by default."
        ),
    ] = None,
):
    """Compare mlipx nodes and visualize the results using ZnDraw."""
    # TODO: allow for glob patterns
    if kwarg is None:
        kwarg = []
    node_names, revs, remotes = [], [], []
    if glob:
        fs = dvc.api.DVCFileSystem()
        with fs.open("zntrack.json", mode="r") as f:
            all_nodes = list(json.load(f).keys())

    for node in nodes:
        # can be name or name@rev or name@remote@rev
        parts = node.split("@")
        if glob:
            filtered_nodes = [x for x in all_nodes if fnmatch.fnmatch(x, parts[0])]
        else:
            filtered_nodes = [parts[0]]
        for x in filtered_nodes:
            node_names.append(x)
            if len(parts) == 1:
                revs.append(None)
                remotes.append(None)
            elif len(parts) == 2:
                revs.append(parts[1])
                remotes.append(None)
            elif len(parts) == 3:
                remotes.append(parts[1])
                revs.append(parts[2])
            else:
                raise ValueError(f"Invalid node format: {node}")

    node_instances = {}
    for node_name, rev, remote in tqdm(
        zip(node_names, revs, remotes), desc="Loading nodes"
    ):
        node_instances[node_name] = zntrack.from_rev(node_name, remote=remote, rev=rev)

    if len(node_instances) == 0:
        typer.echo("No nodes to compare")
        return

    typer.echo(f"Comparing {len(node_instances)} nodes")

    kwargs = {}
    for arg in kwarg:
        key, value = arg.split("=", 1)
        kwargs[key] = value
    result = node_instances[node_names[0]].compare(*node_instances.values(), **kwargs)

    token = token or str(uuid.uuid4())
    typer.echo(f"View the results at {zndraw_url}/token/{token}")
    vis = ZnDraw(zndraw_url, token=token, convert_nan=convert_nan)
    length = len(vis)
    vis.extend(result["frames"])
    del vis[:length]  # temporary fix
    vis.figures = result["figures"]
    if browser:
        webbrowser.open(f"{zndraw_url}/token/{token}")
    if figures_path:
        for desc, fig in result["figures"].items():
            pio.write_json(fig, pathlib.Path(figures_path) / f"{desc}.json")

    vis.socket.sleep(5)
