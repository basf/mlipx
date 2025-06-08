import typing as t

from pydantic import BaseModel, Field, PositiveFloat, RootModel


class BasisSet(BaseModel):
    """Details of the basis set used."""

    type: t.Literal["plane-wave", "gaussian", "numeric-atomic-orbital", "mixed"] = (
        Field(description="Type of basis set.")
    )
    plane_wave_cutoff_eV: PositiveFloat | None = Field(
        None, description="Plane-wave kinetic energy cutoff in eV."
    )
    name: str | None = Field(
        None, description="Name of the basis set (e.g., 'def2-SVP')."
    )


class Pseudopotential(BaseModel):
    """Details of the pseudopotential or effective core potential used."""

    name: str | None = Field(None, description="Identifier for the pseudopotential")


class DispersionCorrection(BaseModel):
    """Details of the dispersion correction applied."""

    scheme: t.Literal[
        "DFT-D2",
        "DFT-D3",
        "DFT-D3(BJ)",
        "DFT-D3(ABC)",
        "DFT-D4",
        "TS",
        "other",
    ] = Field(description="Dispersion correction scheme.")


class DFTCodeInfo(BaseModel):
    """Information about the DFT software used."""

    name: t.Literal[
        "VASP", "ORCA", "CP2K", "QuantumEspresso", "GPAW", "FHI-aims", "other"
    ] = Field(description="Name of the DFT software package.")
    version: str | None = Field(None, description="Version string of the DFT software.")


class DFTMethod(BaseModel):
    """Core DFT method parameters."""

    functional: str = Field(description="Name of the exchange-correlation functional.")


class ConvergenceCriteria(BaseModel):
    """SCF and geometry optimization convergence criteria."""

    scf_energy_threshold: PositiveFloat | None = Field(
        None, description="SCF energy convergence criterion per atom in eV."
    )


class DFTSettings(BaseModel):
    code: DFTCodeInfo | None = Field(
        None, description="Information about the DFT software used."
    )
    method: DFTMethod | None = Field(
        None, description="Core DFT method parameters like functional"
    )
    basis_set: BasisSet | None = Field(None, description="Details of the basis set.")
    pseudopotential: Pseudopotential | None = Field(
        None, description="Details of pseudopotentials, if applicable."
    )
    dispersion_correction: DispersionCorrection | None = Field(
        None, description="Dispersion correction applied."
    )
    convergence_criteria: ConvergenceCriteria | None = Field(
        None, description="Convergence criteria for the calculation."
    )

class PublicDataset(BaseModel):
    name: str = Field(description="Name of the public dataset.")
    file_hash : str = Field(
        description="Hash of the dataset file, used for verification."
    )

class MLIPSpec(BaseModel):
    """MLIP specification for DFT settings."""

    data: DFTSettings | PublicDataset = Field(description="DFT settings used in the MLIP training.")

class MLIPS(RootModel[dict[str, MLIPSpec]]):
    """Root model for MLIP specifications."""

# TODO: the public datasets are stored in a file `datasets.yaml` in this directory.
# The PublicDataset in MLIPS should be written, such that it reads that file
#  and uses Literal types for the dataset names when generating the schema.

class Datasets(RootModel[dict[str, DFTSettings]]):
    """Root model for datasets."""

if __name__ == "__main__":
    # write the json schema to `mlip-schema.json`
    import json
    from pathlib import Path

    file = Path(__file__).parent / "mlips-schema.json"
    file.write_text(json.dumps(MLIPS.model_json_schema(), indent=2))

    file = Path(__file__).parent / "datasets-schema.json"
    file.write_text(json.dumps(Datasets.model_json_schema(), indent=2))
