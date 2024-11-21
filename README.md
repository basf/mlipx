[![PyPI version](https://badge.fury.io/py/mlipx.svg)](https://badge.fury.io/py/mlipx)
[![ZnTrack](https://img.shields.io/badge/Powered%20by-ZnTrack-%23007CB0)](https://zntrack.readthedocs.io/en/latest/)

# Machine-Learned Interatomic Potential eXploration (`mlipx`)

`mlipx` is a Python library designed for evaluating machine-learned interatomic
potentials (MLIPs). It offers a growing set of evaluation methods alongside
powerful visualization and comparison tools.

The goal of `mlipx` is to provide a common platform for MLIP evaluation and to
facilitate sharing results among researchers. This allows you to determine the
applicability of a specific MLIP to your research and compare it against others.

## Installation

Install `mlipx` via pip:

```bash
pip install mlipx
```

## Quickstart

This section provides a brief overview of the core features of mlipx. For more
detailed instructions, visit the [documentation](https://mlipx.readthedocs.io).

### Step 1: Set Up Your Project

Create a new directory and initialize a GIT and DVC repository:

```bash
mkdir relax
cd relax
git init && dvc init
cp /your/data/file.xyz .
dvc add file.xyz
```

### Step 2: Define Your MLIPs

Create a `models.py` file to specify the MLIPs you want to evaluate. For the
[MACE-MP-0](https://github.com/ACEsuit/mace?tab=readme-ov-file#mace-mp-materials-project-force-fields) model this could look like this

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

> [!NOTE]
> `mlipx` utilizes [ASE](https://wiki.fysik.dtu.dk/ase/index.html),
> meaning any ASE-compatible calculator for your MLIP can be used.

### Step 3: Run an Example Recipe

Choose from one of the many
[recipes](https://mlipx.readthedocs.io/en/latest/recipes.html). For example, to
perform a structure optimization, run:

```bash
mlipx recipes relax --datapath file.xyz --repro
mlipx compare --glob '*StructureOptimization'
```

### Visualization Example

Below is an example of the resulting comparison:

![ZnDraw UI](https://github.com/user-attachments/assets/18159cf5-613c-4779-8d52-7c5e37e2a32f#gh-dark-mode-only "ZnDraw UI")
![ZnDraw UI](https://github.com/user-attachments/assets/0d673ef4-0131-4b74-892c-0b848d0669f7#gh-light-mode-only "ZnDraw UI")

## Python API

You can also use all the recipes from the `mlipx` command-line interface
programmatically in Python.

> [!NOTE]
> Whether you use the CLI or the Python API, you must work within a GIT
> and DVC repository. This setup ensures reproducibility and enables automatic
> caching and other features from DVC and ZnTrack.

```python
import mlipx

# Initialize the project
project = mlipx.Project()

# Define an MLIP
mace_mp = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={
        "model": "medium",
    },
)

# Use the MLIP in a structure optimization
with project:
    data = mlipx.LoadDataFile(path="/your/data/file.xyz")
    relax = mlipx.StructureOptimization(
        data=data.frames,
        data_id=-1,
        model=mace_mp,
        fmax=0.1
    )

# Reproduce the project state
project.repro()

# Access the results
print(relax.frames)
# >>> [ase.Atoms(...), ...]
```
