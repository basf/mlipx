import pathlib
import shutil
import subprocess
import typing as t

import jinja2
import typer
from ase.data import chemical_symbols

from mlipx.nodes.filter_dataset import FilteringType

CWD = pathlib.Path(__file__).parent


app = typer.Typer()


def initialize_directory():
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["dvc", "init"], check=True)
    shutil.copy(CWD.parent / "recipes" / "models.py", "models.py")


@app.command()
def elements(
    elements: t.Annotated[list[str], typer.Argument()],
    filtering_type: FilteringType = FilteringType.INCLUSIVE,
):
    for element in elements:
        if element not in chemical_symbols:
            raise ValueError(f"{element} is not a chemical element")
    template = jinja2.Template((CWD / "elements.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(elements=elements, filtering_type=filtering_type.value))


@app.command()
def file(
    datapath: str,
):
    template = jinja2.Template((CWD / "file.py").read_text())
    with open("main.py", "w") as f:
        f.write(template.render(datapath=datapath))
