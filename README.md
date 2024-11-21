[![PyPI version](https://badge.fury.io/py/mlipx.svg)](https://badge.fury.io/py/mlipx)
[![ZnTrack](https://img.shields.io/badge/Powered%20by-ZnTrack-%23007CB0)](https://zntrack.readthedocs.io/en/latest/)

# Machine-Learned Interatomic Potential eXploration

```bash
pip install mlipx
```

`mlipx` is a Python library for the evaluation of machine-learned interatomic
potentials (MLIPs). It provides you with an ever-growing set of evaluation
methods accompanied by comprehensive visualization and comparison tools. The
goal of this project is to provide a common platform for the evaluation of MLIPs
and to facilitate the exchange of evaluation results between researchers.
Ultimately, you should be able to determine the applicability of a given MLIP
for your specific research question and to compare it to other MLIPs.

## Quickstart

This will give you a short overview of core feature of the `mlipx` package. For
more information check out the documentation at https://mlipx.readthedocs.io.

Create a new directory and initialize an GIT and DVC repository

```bash
mkdir relax
cd relax
git init && dvc init
cp /your/data/file.xyz .
```

Then create a `models.py` file to specify the MLIPs you want to evaluate on that
file.

```python
import mlipx

mace_mp = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={
        "model": "medium",
    },
)

MODELS = {"mace_mp": mace_mp}
```

This is the basic structure for the core functionality of `mlipx`. You can now
choose from one of multiple
[recipes](https://mlipx.readthedocs.io/en/latest/recipes.html) to run on your
data file. For this example we will run a structure optimization:

```bash
mlipx recipes relax --datapath DODH_adsorption.xyz --repro
mlipx compare --glob '*StructureOptimization'
```

![ZnDraw UI](https://github.com/user-attachments/assets/18159cf5-613c-4779-8d52-7c5e37e2a32f#gh-dark-mode-only "ZnDraw UI")
![ZnDraw UI](https://github.com/user-attachments/assets/0d673ef4-0131-4b74-892c-0b848d0669f7#gh-light-mode-only "ZnDraw UI")

## Python API

You can make also use of all the recipes provided by the `mlipx` command line
interface through Python directly.

```python
import mlipx

project = mlipx.Project()

mace_mp = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={
        "model": "medium",
    },
)

with project:
    data = mlipx.LoadDataFile(path="/your/data/file.xyz")
    relax = mlipx.StructureOptimization(
        data=data.frames,
        data_id=-1,
        model=mace_mp,
        fmax=0.1
    )

project.repro()

print(relax.frames)
>>> [ase.Atoms(...), ...]
```
