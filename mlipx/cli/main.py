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
from mlipx.spec import MLIPS, Datasets

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
def info():  # noqa: C901
    """Print the version of mlipx and the available models."""
    import mlipx
    from mlipx import __all__
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

    node_names = []
    for name in __all__:
        try:
            obj = getattr(mlipx, name, None)
            if issubclass(obj, zntrack.Node):
                node_names.append(name)
        except (TypeError, ModuleNotFoundError):
            continue  # Not a class

    # Create a nicely styled table with the total count in the title
    nodes_table = Table(
        show_header=False,
        title=f"🔍 Nodes in mlipx [Total: {len(node_names)}]",
    )
    for name in sorted(node_names):
        nodes_table.add_row(name)

    # Display all
    console.print(mlipx_table)
    console.print(py_table)
    console.print(mlip_table)
    console.print(nodes_table)


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


@app.command()
def install_vscode_schema(
    target: Annotated[
        str, typer.Argument(help="Path to the VS Code settings directory")
    ] = ".vscode",
):
    """Configure VS Code to use MLIP schema."""

    vscode_dir = pathlib.Path(target)
    vscode_dir.mkdir(exist_ok=True)

    mlips_schema_path = (vscode_dir / "mlipx-mlips.schema.json").resolve()
    mlips_schema_glob = ["**/*.mlips.yaml", "**/mlips.yaml"]
    datasets_schema_path = (vscode_dir / "mlipx-datasets.schema.json").resolve()
    datasets_schema_glob = ["**/*.datasets.yaml", "**/datasets.yaml"]

    # write the schemas to files
    mlips_schema_path.write_text(json.dumps(MLIPS.model_json_schema(), indent=2))
    datasets_schema_path.write_text(json.dumps(Datasets.model_json_schema(), indent=2))

    settings_path = vscode_dir / "settings.json"

    # Load existing settings
    if settings_path.exists():
        with settings_path.open("r", encoding="utf-8") as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                typer.echo("❌ settings.json is not valid JSON.")
                raise typer.Exit(code=1)
    else:
        settings = {}

    # # Update yaml.schemas
    settings.setdefault("yaml.schemas", {})
    settings["yaml.schemas"][mlips_schema_path.as_posix()] = mlips_schema_glob
    settings["yaml.schemas"][datasets_schema_path.as_posix()] = datasets_schema_glob

    with settings_path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    typer.echo(
        "✅ VS Code schemas from mlipx have been"
        f" configured in {vscode_dir.resolve()}/settings.json"
    )


@app.command(name="serve-broker")
def serve_broker(
    path: Annotated[
        str | None,
        typer.Option(help="IPC path for broker frontend (clients connect here)"),
    ] = None,
):
    """Start the ZeroMQ broker for MLIP workers.

    The broker handles load balancing and routing between clients and workers
    using the LRU (Least Recently Used) pattern.

    Examples
    --------
    Start broker with default path:

        $ mlipx serve-broker

    Start broker with custom path:

        $ mlipx serve-broker --path ipc:///tmp/my-broker.ipc
    """
    from mlipx.serve import run_broker

    typer.echo("Starting MLIP broker...")
    if path:
        typer.echo(f"Broker path: {path}")
    else:
        from mlipx.serve import get_default_broker_path

        typer.echo(f"Broker path: {get_default_broker_path()}")

    run_broker(frontend_path=path)


@app.command()
def serve(
    model_name: Annotated[str, typer.Argument(help="Name of the model to serve")],
    broker: Annotated[
        str | None,
        typer.Option(help="IPC path to broker backend"),
    ] = None,
    models: Annotated[
        pathlib.Path | None,
        typer.Option(help="Path to models.py file containing ALL_MODELS dict"),
    ] = None,
):
    """Start a worker process to serve an MLIP model.

    The worker connects to the broker backend and serves calculations for the
    specified model. Multiple workers can serve the same model for load balancing.

    Examples
    --------
    Serve a single model:

        $ uv run --extra mace mlipx serve mace-mpa-0

    Serve with custom broker path:

        $ uv run --extra mace mlipx serve mace-mpa-0 --broker ipc:///tmp/my-broker-workers.ipc

    Load model from custom models.py file:

        $ uv run --extra mace mlipx serve mace-mpa-0 --models /path/to/models.py

    Run multiple workers for load balancing:

        $ uv run --extra mace mlipx serve mace-mpa-0 &
        $ uv run --extra mace mlipx serve mace-mpa-0 &
        $ uv run --extra mace mlipx serve mace-mpa-0 &
    """
    from mlipx.serve import run_worker

    typer.echo(f"Starting worker for model '{model_name}'...")
    if broker:
        typer.echo(f"Broker backend: {broker}")
    if models:
        typer.echo(f"Loading models from: {models}")

    run_worker(model_name=model_name, backend_path=broker, models_file=models)


@app.command(name="serve-status")
def serve_status(
    broker: Annotated[
        str | None,
        typer.Option(help="IPC path to broker"),
    ] = None,
):
    """Check the status of the MLIP broker and available models.

    Examples
    --------
    Check status with default broker:

        $ mlipx serve-status

    Check status with custom broker path:

        $ mlipx serve-status --broker ipc:///tmp/my-broker.ipc
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from mlipx.serve import get_broker_detailed_status

    console = Console()

    # Get detailed status
    status = get_broker_detailed_status(broker_path=broker)

    # Determine broker path to display
    display_broker_path = status["broker_path"]
    if broker is None:
        display_broker_path = f"{display_broker_path} [dim](default)[/dim]"

    # Create status panel
    if status["broker_running"]:
        broker_status = "[green]✓ Running[/green]"
        panel_style = "green"
    else:
        broker_status = "[red]✗ Not Running[/red]"
        panel_style = "red"

    # Broker info table
    broker_table = Table(show_header=False, box=None, padding=(0, 1))
    broker_table.add_column("Key", style="bold cyan", width=8)
    broker_table.add_column("Value")
    broker_table.add_row("Status", broker_status)
    broker_table.add_row("Path", display_broker_path)

    if status["error"]:
        broker_table.add_row("Error", f"[red]{status['error']}[/red]")

    console.print(
        Panel(
            broker_table,
            title="🔌 Broker Status",
            border_style=panel_style,
            padding=(1, 2),
        )
    )

    # Models panel
    if status["broker_running"] and status["models"]:
        total_workers = sum(
            model_info["worker_count"] for model_info in status["models"].values()
        )

        # Create bullet list of models with worker counts
        models_list = []
        for model_name in sorted(status["models"].keys()):
            model_info = status["models"][model_name]
            worker_count = model_info["worker_count"]
            worker_text = "worker" if worker_count == 1 else "workers"
            models_list.append(
                f"[cyan]•[/cyan] [bold]{model_name}[/bold] [dim]({worker_count} {worker_text})[/dim]"
            )

        models_content = "\n".join(models_list)

        console.print(
            Panel(
                models_content,
                title=f"📊 Available Models ({len(status['models'])} models, {total_workers} workers)",
                border_style="cyan",
                padding=(1, 2),
            )
        )
    elif status["broker_running"]:
        console.print(
            Panel(
                "[yellow]No models currently available[/yellow]\n\n"
                "Start a worker with:\n"
                "  [bold cyan]mlipx serve <model-name>[/bold cyan]",
                title="📊 Available Models",
                border_style="yellow",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                "[red]Cannot query models - broker is not running[/red]\n\n"
                "Start the broker first:\n"
                "  [bold cyan]mlipx serve-broker[/bold cyan]",
                title="📊 Available Models",
                border_style="red",
                padding=(1, 2),
            )
        )
