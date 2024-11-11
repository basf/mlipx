import zntrack
from models import MODELS

import mlipx

project = zntrack.Project()

for model_name, model in MODELS.items():
    with project.group(model_name):
        neb = mlipx.HomonuclearDiatomics(
            elements=["H", "He", "Li"],
            model=model,
            n_points=100,
            min_distance=0.5,
            max_distance=2.0,
        )

project.build()
