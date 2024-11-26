<div align="center">

![Logo](./docs/source/_static/mlipx-dark.svg#gh-dark-mode-only)
![Logo](./docs/source/_static/mlipx-light.svg#gh-light-mode-only)


[![PyPI version](https://badge.fury.io/py/mlipx.svg)](https://badge.fury.io/py/mlipx)
[![ZnTrack](https://img.shields.io/badge/Powered%20by-ZnTrack-%23007CB0)](https://zntrack.readthedocs.io/en/latest/)
[![ZnDraw](https://img.shields.io/badge/works_with-ZnDraw-orange)
](https://github.com/zincware/zndraw)
[![open issues](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/basf/mlipx/issues)


[📘Documentation](https://mlipx.readthedocs.io) |
[🛠️Installation](https://mlipx.readthedocs.io/en/latest/installation.html) |
[📜Recipes](https://mlipx.readthedocs.io/en/latest/recipes.html) |
[🚀Quickstart](https://mlipx.readthedocs.io/en/latest/quickstart.html)
</div>

<div style="text-align: center;">
    <h1>Machine-Learned Interatomic Potential eXploration</h1>
</div>

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

> [!NOTE]
> The `mlipx` package does not include the installation of any MLIP code, as we aim to keep the package as lightweight as possible.
> If you encounter any `ImportError`, you may need to install the additional dependencies manually.

## Quickstart

This section provides a brief overview of the core features of `mlipx`. For more detailed instructions, visit the [documentation](https://mlipx.readthedocs.io).

Most recipes support different input formats, such as data file paths, `SMILES` strings, or Materials Project structure IDs.

> [!NOTE]
> Because `mlipx` uses Git and [DVC](https://dvc.org/doc), you need to create a new project directory to run your experiments in. Here's how to set up your project:
>
> ```bash
> mkdir exp
> cd exp
> git init && dvc init
> ```
> If you want to use datafiles, it is recommend to track them with `dvc add <file>` instead of `git add <file>`.
> ```bash
> cp /your/data/file.xyz .
> dvc add file.xyz
> ```

### Energy-Volume Curve

Compute an energy-volume curve using the `mp-1143` structure from the Materials Project and MLIPs such as `mace-mp`, `sevennet`, and `orb_v2`:

```bash
mlipx recipes ev --models mace_mp,sevennet,orb_v2 --material-ids=mp-1143 --repro
mlipx compare --glob "*EnergyVolumeCurve"
```

> [!NOTE]
> `mlipx` utilizes [ASE](https://wiki.fysik.dtu.dk/ase/index.html),
> meaning any ASE-compatible calculator for your MLIP can be used.
> If we do not provide a preset for your model, you can either adapt the `models.py` file, raise an [issue](https://github.com/basf/mlipx/issues/new) to request support, or submit a pull request to add your model directly.

Below is an example of the resulting comparison:

![ZnDraw UI](https://github.com/user-attachments/assets/2036e6d9-3342-4542-9ddb-bbc777d2b093#gh-dark-mode-only "ZnDraw UI")
![ZnDraw UI](https://github.com/user-attachments/assets/c2479d17-c443-4550-a641-c513ede3be02#gh-light-mode-only "ZnDraw UI")

> [!NOTE]
> Set your default visualizer path using: `export ZNDRAW_URL=http://localhost:1234`.

### Structure Optimization

Compare the performance of different models in optimizing multiple molecular structures from `SMILES` representations:

```bash
mlipx recipes relax --models mace_mp,sevennet,orb_v2 --smiles "CCO,C1=CC2=C(C=C1O)C(=CN2)CCN" --repro
mlipx compare --glob "*0_StructureOptimization"
mlipx compare --glob "*1_StructureOptimization"
```

![ZnDraw UI](https://github.com/user-attachments/assets/7e26a502-3c59-4498-9b98-af8e17a227ce#gh-dark-mode-only "ZnDraw UI")
![ZnDraw UI](https://github.com/user-attachments/assets/a68ac9f5-e3fe-438d-ad4e-88b60499b79e#gh-light-mode-only "ZnDraw UI")

### Nudged Elastic Band (NEB)

Run and compare nudged elastic band (NEB) calculations for a given start and end structure:

```bash
mlipx recipes neb --models mace_mp,sevennet,orb_v2 --datapath ../data/neb_end_p.xyz --repro
mlipx compare --glob "*NEBs"
```

![ZnDraw UI](https://github.com/user-attachments/assets/a2e80caf-dd86-4f14-9101-6d52610b9c34#gh-dark-mode-only "ZnDraw UI")
![ZnDraw UI](https://github.com/user-attachments/assets/0c1eb681-a32c-41c2-a15e-2348104239dc#gh-light-mode-only "ZnDraw UI")


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
