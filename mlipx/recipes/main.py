import pathlib
import shutil
import subprocess
import typing as t

import jinja2
import typer

CWD = pathlib.Path(__file__).parent

app = typer.Typer()


def initialize_directory():
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["dvc", "init"], check=True)


def repro_if_requested(repro: bool):
    if repro:
        subprocess.run(["python", "main.py"], check=True)
        subprocess.run(["dvc", "repro"], check=True)


@app.command()
def relax(
    initialize: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    repro: bool = False,
    models: t.Annotated[t.List[str] | None, typer.Argument()] = None,
):
    if sum([datapath is not None, material_ids is not None, smiles is not None]) == 0:
        raise ValueError(
            "At least one of `datapath`, `material_ids` or `smiles` must be provided."
        )
    datapath_ = None
    material_ids_ = None
    smiles_ = None
    if datapath is not None:
        datapath_ = datapath.split(",")
    if material_ids is not None:
        material_ids_ = material_ids.split(",")
    if smiles is not None:
        smiles_ = smiles.split(",")

    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "relax.py.jinja2").read_text())
    with open("main.py", "w") as f:
        f.write(
            template.render(
                datapath=datapath_, material_ids=material_ids_, smiles=smiles_
            )
        )
        template = jinja2.Template((CWD / "models.py.jinja2").read_text())
        with open("models.py", "w") as f:
            f.write(template.render(models=models))
    repro_if_requested(repro)


@app.command()
def neb(initialize: bool = False, datapath: str = "...", repro: bool = False):
    """Build a NEB recipe."""
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "neb.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))
    repro_if_requested(repro)


@app.command()
def vibrational_analysis(initialize: bool = False, repro: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "vibrational_analysis.py", "main.py")
    repro_if_requested(repro)


@app.command()
def phase_diagram(initialize: bool = False, repro: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "phase_diagram.py", "main.py")
    repro_if_requested(repro)


@app.command()
def pourbaix_diagram(initialize: bool = False, repro: bool = False):
    if initialize:
        initialize_directory()
    shutil.copy(CWD / "pourbaix_diagram.py", "main.py")
    repro_if_requested(repro)


@app.command()
def md(initialize: bool = False, datapath: str = "...", repro: bool = False):
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
    repro_if_requested(repro)


@app.command()
def homonuclear_diatomics(initialize: bool = False, repro: bool = False):
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "homonuclear_diatomics.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render())
    repro_if_requested(repro)


@app.command()
def ev(initialize: bool = False, datapath: str = "...", repro: bool = False):
    """Compute Energy-Volume curves."""
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "energy_volume.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))
    repro_if_requested(repro)


@app.command()
def metrics(
    initialize: bool = False,
    datapath: str = "...",
    isolated_atom_energies: bool = False,
    repro: bool = False,
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
    repro_if_requested(repro)


@app.command()
def invariances(initialize: bool = False, datapath: str = "...", repro: bool = False):
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
    repro_if_requested(repro)
