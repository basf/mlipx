```bash
mlipx recipes vibrational-analysis --models mace_mp,sevennet,orb_v2 --smiles=CO,CCO,CCCO,CCCCO
vim main.py # set system="molecule"
python main.py
dvc repro
mlipx compare --glob "*VibrationalAnalysis"
```
