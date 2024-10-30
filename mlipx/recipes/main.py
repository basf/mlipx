import pathlib
import shutil
import subprocess

import jinja2
from typer import Typer

CWD = pathlib.Path(__file__).parent


app = Typer()


@app.command()
def relax(initialize: bool = False):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    shutil.copy(CWD / "relax.py", "main.py")


@app.command()
def neb(initialize: bool = False, datapath: str = "..."):
    """Build a NEB recipe."""
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    template = jinja2.Template((CWD / "neb.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def vibrational_analysis(initialize: bool = False):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    shutil.copy(CWD / "vibrational_analysis.py", "main.py")


@app.command()
def phase_diagram(initialize: bool = False):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    shutil.copy(CWD / "phase_diagram.py", "main.py")


@app.command()
def pourbaix_diagram(initialize: bool = False):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
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
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    template = jinja2.Template((CWD / "md.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def energy_and_forces(initialize: bool = False, datapath: str = "..."):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    template = jinja2.Template((CWD / "energy_and_forces.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))


@app.command()
def homonuclear_diatomics(initialize: bool = False):
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    template = jinja2.Template((CWD / "homonuclear_diatomics.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render())


@app.command()
def ev(initialize: bool = False):
    """Compute Energy-Volume curves."""
    if initialize:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["dvc", "init"], check=True)
    template = jinja2.Template((CWD / "energy_volume.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render())
