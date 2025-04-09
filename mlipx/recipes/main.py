import json
import os
import pathlib
import subprocess
import typing as t

import jinja2
import typer

CWD = pathlib.Path(__file__).parent

app = typer.Typer()


def initialize_directory():
    """Initialize a Git and DVC repository."""
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["dvc", "init"], check=True)


def render_template(template_name: str, output_name: str, **context):
    """Render a Jinja2 template and write it to a file."""
    template_path = CWD / template_name
    template = jinja2.Template(template_path.read_text())
    with open(output_name, "w") as f:
        f.write(template.render(**context))


def repro_if_requested(repro: bool):
    """Run the repro pipeline if requested."""
    if repro:
        subprocess.run(["python", "main.py"], check=True)
        subprocess.run(["dvc", "repro"], check=True)


def render_models(models: str | None):
    """Render the models.py file if models are specified."""
    if models:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))


def parse_inputs(datapath: str | None, material_ids: str | None, smiles: str | None):
    """Parse and validate input arguments."""
    if not any([datapath, material_ids, smiles]):
        raise ValueError(
            "Provide at least one of `datapath`, `material_ids`, or `smiles`."
        )

    return {
        "datapath": datapath.split(",") if datapath else None,
        "material_ids": material_ids.split(",") if material_ids else None,
        "smiles": smiles.split(",") if smiles else None,
    }


def handle_recipe(
    template_name: str,
    initialize: bool,
    repro: bool,
    datapath: str | None,
    material_ids: str | None,
    smiles: str | None,
    **additional_context,
):
    """Common logic for handling recipes."""
    if initialize:
        initialize_directory()

    inputs = parse_inputs(datapath, material_ids, smiles)
    render_template(template_name, "main.py", **inputs, **additional_context)
    repro_if_requested(repro)


@app.command()
def relax(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Perform a relaxation task."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        CWD / "relax.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def neb(
    initialize: bool = False,
    datapath: str = "...",
    repro: bool = False,
    models: str | None = None,
):
    """Build a NEB recipe."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    if initialize:
        initialize_directory()
    template = jinja2.Template((CWD / "neb.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))
    repro_if_requested(repro)


@app.command()
def vibrational_analysis(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Run vibrational analysis."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "vibrational_analysis.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def phase_diagram(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Build a phase diagram."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "phase_diagram.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def pourbaix_diagram(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Build a Pourbaix diagram."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "pourbaix_diagram.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=None,
    )


@app.command()
def md(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Build an MD recipe."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "md.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def homonuclear_diatomics(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Run homonuclear diatomics calculations."""
    if models is not None:
        models_lst = models.split(",")
        orcashell = ""
        if "orca" in models_lst:
            if "MLIPX_ORCA" not in os.environ:
                orcashell = typer.prompt("Enter the path to the Orca executable")
            else:
                orcashell = None

        render_template(
            CWD / "models.py.jinja2",
            "models.py",
            models=models_lst,
            orcashell=orcashell,
        )

    handle_recipe(
        "homonuclear_diatomics.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def ev(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Compute Energy-Volume curves."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "energy_volume.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def metrics(
    initialize: bool = False,
    datapath: str = "...",
    isolated_atom_energies: bool = False,
    repro: bool = False,
    models: str | None = None,
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
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    template = jinja2.Template((CWD / "metrics.py").read_text())
    with open("main.py", "w") as f:
        f.write(
            template.render(
                datapath=datapath, isolated_atom_energies=isolated_atom_energies
            )
        )
    repro_if_requested(repro)


@app.command()
def invariances(
    initialize: bool = False,
    repro: bool = False,
    datapath: str | None = None,
    material_ids: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Test rotational, permutational, and translational invariance."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    handle_recipe(
        "invariances.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=datapath,
        material_ids=material_ids,
        smiles=smiles,
    )


@app.command()
def adsorption(
    initialize: bool = False,
    repro: bool = False,
    slab_config: str | None = None,
    slab_material_id: str | None = None,
    smiles: str | None = None,
    models: t.Annotated[str | None, typer.Option()] = None,
):
    """Test rotational, permutational, and translational invariance."""
    if models is not None:
        render_template(CWD / "models.py.jinja2", "models.py", models=models.split(","))
    if slab_config is not None:
        slab_config = json.loads(slab_config)
    handle_recipe(
        "adsorption.py.jinja2",
        initialize=initialize,
        repro=repro,
        datapath=None,
        material_ids=None,
        smiles=smiles,
        slab_config=slab_config,
    )
