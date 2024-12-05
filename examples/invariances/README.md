```bash
mlipx recipes invariances --models mace_mp,sevennet,orb_v2,chgnet,mattersim --material-ids=mp-1143 --repro
mlipx compare --glob "*RotationalInvariance"
mlipx compare --glob "*TranslationalInvariance"
mlipx compare --glob "*PermutationInvariance"
```
