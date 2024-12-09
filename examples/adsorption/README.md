```bash
mlipx recipes adsorption --models mace_mp,sevennet,orb_v2,mattersim --slab-config '{"crystal": "fcc111", "symbol": "Cu", "size": [3,4,4]}' --smiles CCO --repro
mlipx compare --glob "*RelaxAdsorptionConfigs"
```
