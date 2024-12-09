import mlipx

model = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={"model": "medium"},
)


project = mlipx.Project()


# from m in metals
# from a in adsorbates
# with project.group(m,a)

with project.group('initialize'):
    slab = mlipx.BuildASEslab(crystal='fcc111', symbol='Cu', size=(3,4,4))
    
    adsorbates = mlipx.Smiles2Conformers(smiles='CO', num_confs=1)
    
    ads_slabs = mlipx.RelaxAdsorptionConfigs(
        slabs=slab.frames,
        adsorbates=adsorbates.frames,
        model=model,
        )
    
    
    
    

project.repro()