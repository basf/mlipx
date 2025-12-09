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


def _get_available_models() -> dict:
    """Load available models from the default models template."""
    try:
        import jinja2

        import mlipx
        from mlipx import recipes

        recipes_path = pathlib.Path(recipes.__file__).parent
        template = jinja2.Template((recipes_path / "models.py.jinja2").read_text())
        rendered_code = template.render(models=[])

        namespace = {"mlipx": mlipx}
        exec(rendered_code, namespace)

        all_models = namespace.get("ALL_MODELS", {})
        return {name: model.available for name, model in all_models.items()}
    except Exception:
        return {}


@app.command()
def info():  # noqa: C901
    """Print the version of mlipx and the available models."""
    import mlipx
    from mlipx import __all__

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
    available_models = _get_available_models()
    mlip_table = Table(title="🧠 MLIP Codes", box=box.ROUNDED)
    mlip_table.add_column("Model", style="bold")
    mlip_table.add_column("Available", style="bold")

    for model in sorted(available_models):
        status = available_models[model]
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
    frontend: Annotated[
        str | None,
        typer.Option(help="IPC path for broker frontend (clients connect here)"),
    ] = None,
    backend: Annotated[
        str | None,
        typer.Option(help="IPC path for broker backend (workers connect here)"),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option(help="Worker timeout in seconds (default: 30.0)"),
    ] = 30.0,
    queue_timeout: Annotated[
        float,
        typer.Option(help="Request queue timeout in seconds (default: 60.0)"),
    ] = 60.0,
    log_level: Annotated[
        str,
        typer.Option(help="Log level (default: INFO)"),
    ] = "INFO",
    autostart: Annotated[
        bool,
        typer.Option(
            "--autostart", help="Enable on-demand worker spawning via manager"
        ),
    ] = False,
):
    """Start the aserpc broker for MLIP workers.

    The broker handles load balancing and routing between clients and workers.
    This is a wrapper around 'aserpc broker'.

    Examples
    --------
    Start broker with default settings:

        $ mlipx serve-broker

    Start broker with on-demand autostart (spawns workers when requested):

        $ mlipx serve-broker --autostart

    Start broker with custom timeout:

        $ mlipx serve-broker --timeout 60.0
    """
    import subprocess
    import time

    from mlipx.serve import is_broker_running

    broker_cmd = ["aserpc", "broker"]

    if frontend:
        broker_cmd.extend(["--frontend", frontend])
    if backend:
        broker_cmd.extend(["--backend", backend])
    broker_cmd.extend(["--timeout", str(timeout)])
    broker_cmd.extend(["--queue-timeout", str(queue_timeout)])
    broker_cmd.extend(["--log-level", log_level])

    if not autostart:
        # Simple mode: just run the broker
        typer.echo("Starting aserpc broker...")
        typer.echo(f"Command: {' '.join(broker_cmd)}")
        subprocess.run(broker_cmd)
        return

    # Autostart mode: start broker + manager for on-demand worker spawning
    manager_cmd = ["aserpc", "manager", "--log-level", log_level]

    typer.echo("Starting aserpc broker + manager (on-demand worker spawning)...")
    typer.echo(f"Broker command: {' '.join(broker_cmd)}")
    typer.echo(f"Manager command: {' '.join(manager_cmd)}")

    # Start broker in background
    broker_proc = subprocess.Popen(broker_cmd)

    # Wait for broker to be ready
    typer.echo("Waiting for broker to start...")
    for _ in range(30):
        time.sleep(0.5)
        if is_broker_running():
            break
    else:
        typer.echo("[red]Broker failed to start within 15 seconds[/red]")
        broker_proc.terminate()
        raise typer.Exit(1)

    typer.echo("[green]Broker is running[/green]")

    # Start manager (discovers spawn configs from entry points)
    manager_proc = subprocess.Popen(manager_cmd)
    typer.echo("[green]Manager is running (workers will spawn on demand)[/green]")
    typer.echo("Press Ctrl+C to stop\n")

    # Wait for broker (blocking)
    try:
        broker_proc.wait()
    except KeyboardInterrupt:
        typer.echo("\nShutting down...")
        manager_proc.terminate()
        broker_proc.terminate()


@app.command()
def serve(
    model_name: Annotated[str, typer.Argument(help="Name of the model to serve")],
    broker: Annotated[
        str | None,
        typer.Option(help="IPC path to broker backend"),
    ] = None,
    idle_timeout: Annotated[
        int,
        typer.Option(help="Idle timeout in seconds (default: 300)"),
    ] = 300,
    heartbeat: Annotated[
        float,
        typer.Option(help="Heartbeat interval in seconds (default: 5.0)"),
    ] = 5.0,
    log_level: Annotated[
        str,
        typer.Option(help="Log level (default: INFO)"),
    ] = "INFO",
):
    """Start an aserpc worker to serve an MLIP model.

    The worker connects to the broker backend and serves calculations for the
    specified model. Multiple workers can serve the same model for load balancing.

    The worker will automatically shut down after the idle timeout period.
    This is a wrapper around 'aserpc worker' with smart dependency resolution.

    Examples
    --------
    Serve a model:

        $ mlipx serve mace-mpa-0

    Serve with custom timeout:

        $ mlipx serve mace-mpa-0 --idle-timeout 600  # 10 minutes

    Serve with custom broker path:

        $ mlipx serve mace-mpa-0 --broker ipc:///tmp/my-broker-backend.ipc

    Run multiple workers for load balancing:

        $ mlipx serve mace-mpa-0 &
        $ mlipx serve mace-mpa-0 &
        $ mlipx serve mace-mpa-0 &
    """
    import subprocess

    from mlipx.serve import build_worker_command, get_model_extras

    # Get extras for this model
    model_extras = get_model_extras(model_name)

    # Build command with smart dependency resolution
    cmd, method = build_worker_command(
        model_name=model_name,
        model_extras=model_extras,
        idle_timeout=idle_timeout,
        heartbeat=heartbeat,
        log_level=log_level,
    )

    # Add broker if specified
    if broker:
        cmd.extend(["--broker", broker])

    typer.echo(f"Starting aserpc worker for model '{model_name}'...")
    typer.echo(f"Dependency resolution: {method}")
    typer.echo(f"Command: {' '.join(cmd)}")

    subprocess.run(cmd)


def _format_worker_info(model_name: str, worker_info: dict | int) -> tuple[str, int]:
    """Format worker info for display and return (formatted_line, count)."""
    if isinstance(worker_info, dict):
        count = worker_info.get("total", 0)
        idle = worker_info.get("idle", 0)
        busy = worker_info.get("busy", 0)
        status_text = f": {idle} idle, {busy} busy"
    else:
        count = worker_info
        status_text = ""

    worker_text = "worker" if count == 1 else "workers"
    line = (
        f"[cyan]•[/cyan] [bold]{model_name}[/bold] "
        f"[dim]({count} {worker_text}{status_text})[/dim]"
    )
    return line, count


def _display_workers_panel(console, workers: dict) -> None:
    """Display panel showing active workers."""
    from rich.panel import Panel

    total_workers = 0
    models_list = []
    for model_name in sorted(workers.keys()):
        line, count = _format_worker_info(model_name, workers[model_name])
        models_list.append(line)
        total_workers += count

    title = f"Active Workers ({len(workers)} models, {total_workers} workers)"
    console.print(
        Panel("\n".join(models_list), title=title, border_style="cyan", padding=(1, 2))
    )


@app.command(name="serve-status")
def serve_status(
    shutdown: Annotated[
        bool,
        typer.Option(
            "--shutdown",
            help="Shutdown the broker and all workers gracefully",
        ),
    ] = False,
):
    """Check the status of the aserpc broker and available models.

    Examples
    --------
    Check status:

        $ mlipx serve-status

    Shutdown the broker and all workers:

        $ mlipx serve-status --shutdown

    List available calculators:

        $ aserpc list
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Handle shutdown first
    if shutdown:
        try:
            from aserpc import shutdown_workers

            shutdown_workers()
            console.print("[green]✓ Shutdown signal sent to workers[/green]")
        except Exception as e:
            console.print(f"[red]✗ Shutdown failed:[/red] {e}")
        return

    # Get broker status
    try:
        from aserpc import broker_status

        status = broker_status()
        broker_running = status is not None
        error_msg = None
    except Exception as e:
        broker_running = False
        status = None
        error_msg = str(e)

    # Broker info table
    broker_table = Table(show_header=False, box=None, padding=(0, 1))
    broker_table.add_column("Key", style="bold cyan", width=10)
    broker_table.add_column("Value")

    if broker_running:
        broker_table.add_row("Status", "[green]✓ Running[/green]")
        panel_style = "green"
    else:
        broker_table.add_row("Status", "[red]✗ Not Running[/red]")
        broker_table.add_row("Error", f"[red]{error_msg or 'Broker not running'}[/red]")
        panel_style = "red"

    console.print(
        Panel(
            broker_table,
            title="Broker Status",
            border_style=panel_style,
            padding=(1, 2),
        )
    )

    # Workers panel
    if broker_running and status:
        workers = status.get("workers", {})
        if workers:
            _display_workers_panel(console, workers)
        else:
            console.print(
                Panel(
                    "[yellow]No workers currently running[/yellow]\n\n"
                    "Start a worker with:\n"
                    "  [bold cyan]mlipx serve <model-name>[/bold cyan]\n"
                    "  [bold cyan]aserpc worker <model-name>[/bold cyan]\n\n"
                    "List available calculators with:\n"
                    "  [bold cyan]aserpc list[/bold cyan]",
                    title="Active Workers",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )
    elif not broker_running:
        console.print(
            Panel(
                "[red]Cannot query workers - broker is not running[/red]\n\n"
                "Start the broker first:\n"
                "  [bold cyan]mlipx serve-broker[/bold cyan]\n"
                "  [bold cyan]aserpc broker[/bold cyan]",
                title="Active Workers",
                border_style="red",
                padding=(1, 2),
            )
        )
