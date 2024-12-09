import mlipx

model = mlipx.GenericASECalculator(
    module="mace.calculators",
    class_name="mace_mp",
    device="auto",
    kwargs={"model": "medium"},
)

sevnet = mlipx.GenericASECalculator(
    module="sevenn.sevennet_calculator",
    class_name="SevenNetCalculator",
    device="auto",
    kwargs={"model": "7net-0"},
)


project = mlipx.Project()


# from m in metals
# from a in adsorbates
# with project.group(m,a)

with project.group("initialize"):
    slab = mlipx.BuildASEslab(crystal="fcc111", symbol="Cu", size=(3, 4, 4))

    adsorbates = mlipx.Smiles2Conformers(smiles="CO", num_confs=1)


with project.group("mace"):
    ads_slabs = mlipx.RelaxAdsorptionConfigs(
        slabs=slab.frames,
        adsorbates=adsorbates.frames,
        model=model,
    )


with project.group("sevenn"):
    ads_slabs = mlipx.RelaxAdsorptionConfigs(
        slabs=slab.frames,
        adsorbates=adsorbates.frames,
        model=sevnet,
    )

project.repro()
