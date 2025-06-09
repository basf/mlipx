import warnings

import pytest

import mlipx
from mlipx.spec import compare_specs


def test_relax_compare(proj_path):
    project = mlipx.Project()

    mace_mpa = mlipx.GenericASECalculator(
        module="mace.calculators",
        class_name="mace_mp",
        device="auto",
        kwargs={
            "model": "medium",
        },
        spec="mace-mpa-0",
    )

    mace_off = mlipx.GenericASECalculator(
        module="mace.calculators",
        class_name="mace_off",
        device="auto",
        kwargs={
            "model": "medium",
        },
        spec="mace-off",
    )

    mace_mpa_spec = mace_mpa.get_spec()
    mace_off_spec = mace_off.get_spec()

    assert compare_specs({"mace-mpa-0": mace_mpa_spec, "mace-off": mace_off_spec}) == {
        ("mace-mpa-0", "mace-off"): {
            "data.basis_set.name": {
                "mace-mpa-0": None,
                "mace-off": "def2-TZVPPD",
            },
            "data.basis_set.type": {
                "mace-mpa-0": None,
                "mace-off": "plane-wave",
            },
            "data.code": {
                "mace-mpa-0": "VASP",
                "mace-off": "PSI4",
            },
            "data.dispersion_correction.type": {
                "mace-mpa-0": None,
                "mace-off": "DFT-D3(BJ)",
            },
            "data.method.functional": {
                "mace-mpa-0": "PBE+U",
                "mace-off": "ωB97M",
            },
        },
    }

    with project:
        struct = mlipx.Smiles2Conformers(
            smiles="CCO",
            num_confs=10,
        )
    with project.group(mace_mpa.spec):
        m1 = mlipx.StructureOptimization(
            data=struct.frames,
            model=mace_mpa,
        )
        m1b = mlipx.StructureOptimization(
            data=struct.frames,
            model=mace_mpa,
        )
    with project.group(mace_off.spec):
        m2 = mlipx.StructureOptimization(
            data=struct.frames,
            model=mace_off,
        )

    project.repro()

    with pytest.warns(UserWarning, match="Found differences in specs for nodes:"):
        _ = mlipx.StructureOptimization.compare(m1, m2)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _ = mlipx.StructureOptimization.compare(
            m1,
            m1b,
        )
