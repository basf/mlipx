from pathlib import Path

import jinja2

import mlipx
from mlipx import recipes

AVAILABLE_MODELS = {}

RECIPES_PATH = Path(recipes.__file__).parent
template = jinja2.Template((RECIPES_PATH / "models.py.jinja2").read_text())

rendered_code = template.render(models=[])

# Prepare a namespace and execute the rendered code into it
namespace = {"mlipx": mlipx}  # replace with your actual mlipx
exec(rendered_code, namespace)

# Access ALL_MODELS and MODELS
all_models = namespace["ALL_MODELS"]

AVAILABLE_MODELS = {
    model_name: model.available for model_name, model in all_models.items()
}
