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


def _get_local_pyproject_extras() -> set[str]:
    """Get optional-dependencies (extras) from local pyproject.toml if it exists.

    Returns
    -------
    set[str]
        Set of extra names defined in the local pyproject.toml,
        or empty set if not found.
    """
    pyproject_path = pathlib.Path("pyproject.toml")
    if not pyproject_path.exists():
        return set()

    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        try:
            import tomli as tomllib
        except ImportError:
            return set()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        return set(optional_deps.keys())
    except Exception:
        return set()


def _get_mlipx_package_spec(extras: list[str]) -> str:
    """Build a package spec for uvx based on mlipx version.

    For release versions (e.g., "0.1.6"), uses PyPI with pinned version.
    For dev versions, uses the "Source Commit" URL from package metadata.

    Parameters
    ----------
    extras : list[str]
        List of extras to include (e.g., ["mace", "serve"]).

    Returns
    -------
    str
        Package specification for uvx --from.
    """
    import mlipx

    mlipx_version = mlipx.__version__
    extras_str = ",".join(extras)

    if mlipx_version and ("+" in mlipx_version or ".dev" in mlipx_version):
        # Dev version - get commit URL from package metadata
        metadata = importlib.metadata.metadata("mlipx")
        # Look for "Source Commit" URL which contains the commit hash
        for key, value in metadata.items():
            if key == "Project-URL" and value.startswith("Source Commit,"):
                # Format: "Source Commit, https://github.com/basf/mlipx/tree/abc123"
                url = value.split(", ", 1)[1]
                # Extract commit hash from URL
                commit_hash = url.rstrip("/").split("/")[-1]
                return (
                    f"mlipx[{extras_str}] @ "
                    f"git+https://github.com/basf/mlipx@{commit_hash}"
                )
        # No Source Commit URL found, use latest from PyPI
        return f"mlipx[{extras_str}]"
    elif mlipx_version:
        # Release version, use PyPI with pinned version
        return f"mlipx[{extras_str}]=={mlipx_version}"
    else:
        # No version available, use latest from PyPI
        return f"mlipx[{extras_str}]"


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
    model_names: Annotated[
        list[str] | None,
        typer.Argument(
            help="Model names to serve (optional, defaults to all models in models.py)"
        ),
    ] = None,
    path: Annotated[
        str | None,
        typer.Option(help="IPC path for broker frontend (clients connect here)"),
    ] = None,
    autostart: Annotated[
        bool,
        typer.Option(help="Enable automatic worker startup on demand"),
    ] = False,
    models: Annotated[
        pathlib.Path | None,
        typer.Option(
            help="Path to models.py file. If not specified, searches upward from "
            "current directory for models.py, or uses built-in defaults."
        ),
    ] = None,
    worker_timeout: Annotated[
        int,
        typer.Option(
            help="Idle timeout for auto-started workers in seconds (default: 300)"
        ),
    ] = 300,
    worker_start_timeout: Annotated[
        int,
        typer.Option(
            help="Maximum time to wait for worker startup in seconds (default: 60)"
        ),
    ] = 60,
):
    """Start the ZeroMQ broker for MLIP workers.

    The broker handles load balancing and routing between clients and workers
    using the LRU (Least Recently Used) pattern.

    Model Discovery:
    ----------------
    If --models is not specified, mlipx searches for models.py:
    1. MLIPX_MODELS environment variable
    2. models.py in current or parent directories (must contain ALL_MODELS)
    3. Built-in package defaults

    Examples
    --------
    Start broker with autostart (spawns workers on demand):

        $ mlipx serve-broker --autostart

    Serve only specific models:

        $ mlipx serve-broker --autostart mace-mpa-0 orb-v2

    Use explicit models file:

        $ mlipx serve-broker --autostart --models /path/to/models.py

    Start basic broker (no autostart):

        $ mlipx serve-broker

    Start broker with custom path:

        $ mlipx serve-broker --path ipc:///tmp/my-broker.ipc
    """
    if autostart:
        from mlipx.serve import discover_models_file, run_autostart_broker

        # Discover models file
        models_path, source = discover_models_file(models)
        typer.echo(f"Models file: {models_path} ({source})")

        typer.echo("Starting MLIP broker with autostart...")
        if path:
            typer.echo(f"Broker path: {path}")
        else:
            from mlipx.serve import get_default_broker_path

            typer.echo(f"Broker path: {get_default_broker_path()}")
        typer.echo(f"Worker idle timeout: {worker_timeout}s")
        typer.echo(f"Worker startup timeout: {worker_start_timeout}s")
        if model_names:
            typer.echo(f"Serving models: {', '.join(model_names)}")

        run_autostart_broker(
            frontend_path=path,
            models_file=models_path,
            worker_timeout=worker_timeout,
            worker_start_timeout=worker_start_timeout,
            allowed_models=model_names,
        )
    else:
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
        typer.Option(
            help="Path to models.py file. If not specified, searches upward from "
            "current directory for models.py, or uses built-in defaults."
        ),
    ] = None,
    no_uv: Annotated[
        bool,
        typer.Option(help="Disable UV wrapper (already in correct environment)"),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(help="Idle timeout in seconds (default: 300)"),
    ] = 300,
):
    """Start a worker process to serve an MLIP model.

    The worker connects to the broker backend and serves calculations for the
    specified model. Multiple workers can serve the same model for load balancing.

    The worker will automatically shut down after the timeout period of inactivity.
    The timeout resets with every incoming calculation request.

    Model Discovery:
    ----------------
    If --models is not specified, mlipx searches for models.py:
    1. MLIPX_MODELS environment variable
    2. models.py in current or parent directories (must contain ALL_MODELS)
    3. Built-in package defaults

    Examples
    --------
    Serve with auto-detected dependencies:

        $ uv run mlipx serve mace-mpa-0
        # Internally becomes: uv run --extra mace mlipx serve mace-mpa-0 --no-uv

    Serve with custom timeout:

        $ uv run mlipx serve mace-mpa-0 --timeout 600  # 10 minutes

    Disable UV wrapper (already in correct environment):

        $ uv run --extra mace mlipx serve mace-mpa-0 --no-uv

    Serve with custom broker path:

        $ uv run mlipx serve mace-mpa-0 --broker ipc:///tmp/my-broker-workers.ipc

    Load model from custom models.py file:

        $ uv run mlipx serve mace-mpa-0 --models /path/to/models.py

    Run multiple workers for load balancing:

        $ uv run mlipx serve mace-mpa-0 &
        $ uv run mlipx serve mace-mpa-0 &
        $ uv run mlipx serve mace-mpa-0 &
    """
    import os
    import shutil

    from mlipx.serve import discover_models_file
    from mlipx.serve.worker import load_models_from_file, run_worker

    # Discover models file
    models_path, source = discover_models_file(models)

    all_models = load_models_from_file(models_path)

    if model_name not in all_models:
        from rich.console import Console

        console = Console(stderr=True)
        console.print(
            f"[red]Error:[/red] Model '{model_name}' not found in {models_path}"
        )
        available = ", ".join(sorted(all_models.keys()))
        console.print(f"[dim]Available models:[/dim] {available}")
        raise typer.Exit(1)

    model = all_models[model_name]

    # Check if we need to wrap with UV
    needs_uv_wrap = (
        hasattr(model, "extra")
        and model.extra
        and not no_uv
        and not os.getenv("_MLIPX_SERVE_UV_WRAPPED")
    )

    if needs_uv_wrap:
        # Check if uv is available
        uv_path = shutil.which("uv")
        if not uv_path:
            from rich.console import Console

            console = Console(stderr=True)
            console.print(
                "[yellow]Warning:[/yellow] Model specifies 'extra' dependencies "
                "but 'uv' is not available. Proceeding without UV wrapper."
            )
            console.print("[dim]Install uv with: pip install uv[/dim]")
        else:
            from rich.console import Console

            console = Console(stderr=True)

            # Smart detection: check if extras exist in local pyproject.toml
            local_extras = _get_local_pyproject_extras()
            required_extras = set(model.extra)
            extras_str = ", ".join(sorted(required_extras))

            console.print(
                f"[dim]Checking local pyproject.toml for extras: {extras_str}[/dim]"
            )

            if required_extras.issubset(local_extras):
                # Use uv run --extra (extras available in local project)
                console.print(
                    "[dim]Found in local project, using: uv run --extra[/dim]"
                )
                cmd = ["uv", "run"]
                for extra_dep in model.extra:
                    cmd.extend(["--extra", extra_dep])
                cmd.extend(["mlipx", "serve", model_name, "--no-uv"])
            else:
                # Use uvx --from mlipx[extras,serve] (extras from mlipx package)
                console.print(
                    "[dim]Not found locally, using mlipx package extras via uvx[/dim]"
                )
                pkg_spec = _get_mlipx_package_spec(list(model.extra) + ["serve"])
                console.print(f"[dim]Package spec: {pkg_spec}[/dim]")
                cmd = [
                    "uvx",
                    "--from",
                    pkg_spec,
                    "mlipx",
                    "serve",
                    model_name,
                    "--no-uv",
                ]

            if broker:
                cmd.extend(["--broker", broker])
            cmd.extend(["--timeout", str(timeout)])
            # Pass the discovered models file to the wrapped process
            cmd.extend(["--models", str(models_path)])

            # Prevent infinite recursion
            os.environ["_MLIPX_SERVE_UV_WRAPPED"] = "1"

            # Print to stderr so it doesn't interfere with stdout
            # The child process will inherit stdin/stdout/stderr as-is
            if sys.stderr.isatty():
                # In TTY mode, use rich formatting
                from rich.console import Console

                console = Console(stderr=True)
                console.print(f"[dim]Starting with dependencies: {' '.join(cmd)}[/dim]")
            else:
                # Non-TTY mode, simple message to stderr
                print(f"Starting with dependencies: {' '.join(cmd)}", file=sys.stderr)

            os.execvp(cmd[0], cmd)  # Replace current process
            return  # Never reached

    # Normal serve execution
    typer.echo(f"Starting worker for model '{model_name}'...")
    typer.echo(f"Models file: {models_path} ({source})")
    if broker:
        typer.echo(f"Broker backend: {broker}")
    typer.echo(f"Worker timeout: {timeout}s")

    run_worker(
        model_name=model_name,
        backend_path=broker,
        models_file=models_path,
        timeout=timeout,
    )


@app.command(name="serve-status")
def serve_status(  # noqa: C901
    broker: Annotated[
        str | None,
        typer.Option(help="IPC path to broker"),
    ] = None,
    shutdown: Annotated[
        bool,
        typer.Option(
            "--shutdown",
            help="Shutdown the broker and all workers gracefully",
        ),
    ] = False,
):
    """Check the status of the MLIP broker and available models.

    Examples
    --------
    Check status with default broker:

        $ mlipx serve-status

    Check status with custom broker path:

        $ mlipx serve-status --broker ipc:///tmp/my-broker.ipc

    Shutdown the broker and all workers:

        $ mlipx serve-status --shutdown
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from mlipx.serve import get_broker_detailed_status, shutdown_broker

    console = Console()

    # Handle shutdown first
    if shutdown:
        result = shutdown_broker(broker_path=broker)
        if result["success"]:
            console.print("[green]✓ Broker shutdown initiated[/green]")
            console.print(f"[dim]{result['message']}[/dim]")
        elif result["error"]:
            console.print(f"[red]✗ Shutdown failed:[/red] {result['error']}")
        else:
            console.print("[red]✗ Shutdown failed[/red]")
        return

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
    broker_table.add_column("Key", style="bold cyan", width=10)
    broker_table.add_column("Value")
    broker_table.add_row("Status", broker_status)
    broker_table.add_row("Path", display_broker_path)

    if status["broker_running"]:
        autostart_status = (
            "[green]✓ Enabled[/green]" if status["autostart"] else "[dim]Disabled[/dim]"
        )
        broker_table.add_row("Autostart", autostart_status)

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
                f"[cyan]•[/cyan] [bold]{model_name}[/bold] "
                f"[dim]({worker_count} {worker_text})[/dim]"
            )

        models_content = "\n".join(models_list)

        # Show autostart info if enabled
        if status["autostart"] and status["autostart_models"]:
            # Find models that are available via autostart but not currently running
            running_models = set(status["models"].keys())
            autostart_only = sorted(set(status["autostart_models"]) - running_models)

            if autostart_only:
                models_content += (
                    "\n\n[dim]Additional models available via autostart:[/dim]"
                )
                for model_name in autostart_only:
                    models_content += f"\n[dim][cyan]•[/cyan] {model_name}[/dim]"

        num_models = len(status["models"])
        title = f"📊 Available Models ({num_models} models, {total_workers} workers)"
        console.print(
            Panel(
                models_content,
                title=title,
                border_style="cyan",
                padding=(1, 2),
            )
        )
    elif status["broker_running"]:
        if status["autostart"] and status["autostart_models"]:
            # Show autostart models when enabled
            autostart_list = []
            for model_name in sorted(status["autostart_models"]):
                autostart_list.append(f"[cyan]•[/cyan] {model_name}")

            autostart_content = "\n".join(autostart_list)
            num_autostart = len(status["autostart_models"])
            message = (
                "[yellow]No workers currently running[/yellow]\n\n"
                "[bold]Autostart enabled[/bold] - workers will start "
                "automatically on first use.\n\n"
                f"[dim]Available models for autostart ({num_autostart}):[/dim]\n"
                f"{autostart_content}"
            )
        else:
            message = (
                "[yellow]No models currently available[/yellow]\n\n"
                "Start a worker with:\n"
                "  [bold cyan]mlipx serve <model-name>[/bold cyan]"
            )

        console.print(
            Panel(
                message,
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
