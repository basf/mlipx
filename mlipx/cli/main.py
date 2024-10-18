import uuid

import typer
import zntrack
from tqdm import tqdm
from typing_extensions import Annotated
from zndraw import ZnDraw

app = typer.Typer()


@app.command()
def main():
    typer.echo("Hello World")


@app.command()
def compare(
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
):
    """Compare mlipx nodes and visualize the results using ZnDraw."""
    if kwarg is None:
        kwarg = []
    node_names, revs, remotes = [], [], []
    # TODO support wild cards
    for node in nodes:
        # can be name or name@rev or name@remote@rev
        parts = node.split("@")
        node_names.append(parts[0])
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

    token = token or uuid.uuid4().hex
    vis = ZnDraw(zndraw_url, token=token)
    vis.extend(result["frames"])
    del vis[0]
    vis.figures = result["figures"]
    typer.echo(f"View the results at {zndraw_url}/token/{token}")
    vis.socket.sleep(5)
