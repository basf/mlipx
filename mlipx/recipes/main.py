import pathlib
import shutil
import subprocess

import jinja2
from typer import Typer

CWD = pathlib.Path(__file__).parent


app = Typer()


def initialize_directory():
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["dvc", "init"], check=True)
    shutil.copy(CWD / "models.py", "models.py")


@app.command()
def relax(initialize: bool = False, datapath: str = "..."):
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "relax.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def neb(initialize: bool = False, datapath: str = "..."):
    """Build a NEB recipe."""
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "neb.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def vibrational_analysis(initialize: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "vibrational_analysis.py", "main.py")


@app.command()
def phase_diagram(initialize: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "phase_diagram.py", "main.py")


@app.command()
def pourbaix_diagram(initialize: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "pourbaix_diagram.py", "main.py")


@app.command()
def md(initialize: bool = False, datapath: str = "..."):
    """Build an MD recipe.

    Parameters
    ----------
    initialize : bool
        Initialize a git and dvc repository.
    datapath : str
        Path to the data directory.
    """
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "md.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def homonuclear_diatomics(initialize: bool = False):
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "homonuclear_diatomics.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render())


@app.command()
def ev(initialize: bool = False):
    """Compute Energy-Volume curves."""
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "energy_volume.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render())


@app.command()
def metrics(
    initialize: bool = False,
    datapath: str = "...",
    isolated_atom_energies: bool = False,
):
    """Compute Energy and Force Metrics.

    Parameters
    ----------
    initialize : bool
        Initialize a git and dvc repository.
    datapath : str
        Path to the data directory.
    isolated_atom_energies: bool
        Compute metrics based on isolated atom energies.
    """
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "metrics.py").read_text())
    with open("main.py", "w") as f:
        f.write(
            template.render(
                datapath=datapath, isolated_atom_energies=isolated_atom_energies
            )
        )


@app.command()
def invariances(initialize: bool = False, datapath: str = "..."):
    """Test rotational, permutational and translational invariance.

    Parameters
    ----------
    initialize : bool
        Initialize a git and dvc repository.
    datapath : str
        Path to the data directory.
    """
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "invariances.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))
