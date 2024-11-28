# Jinja2 Templating

We use `recipe.py.jinja2` templates for generating the `main.py` and `models.py` file from the CLI.
For new Nodes, once you added them to `mlipx/nodes/<your-node>.py` and updated the `mlipx/__init__.pyi` you might want to create a new template and update the CLI in `main.py`.

If you want to introduce a new model, you might want to adapt `models.py.jinja2` and the `main.py` as well.
