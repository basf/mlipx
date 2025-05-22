# MLIPX Contribution guidelines

## Adding a new MLIP

1. Create a new entry in `[project.optional-dependencies]` in the `pyproject.toml`. Configure `[tool.uv]:conflicts` if necessary.
1. Add your model to `mlipx/recipes/models.py.jinja2` to the `ALL_MODELS` dictionary.
