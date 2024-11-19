import os

import zntrack
from models import MODELS

import mlipx

DATAPATH = "../data/LiMnO_mp_small_vasp_sp.xyz"
os.environ["MP_API_KEY"] = "MuO8J79CEdO7NHXouX976bNDMtd6KkiA"

project = zntrack.Project()

with project.group("initialize"):
    data = mlipx.LoadDataFile(path=DATAPATH)

for model_name, model in MODELS.items():
    with project.group(model_name):
        pd = mlipx.PourbaixDiagram(data=data.frames, model=model, pH=1.0, V=1.8)

project.build()
