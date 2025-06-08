import typing as t
from pathlib import Path
import json
import yaml
from pydantic import BaseModel, Field, PositiveFloat, RootModel
from typing import Literal, Union, Annotated


class BasisSet(BaseModel):
    """Details of the basis set used."""
    type: Literal["plane-wave", "gaussian", "numeric-atomic-orbital", "mixed"] = Field(description="Type of basis set.")
    plane_wave_cutoff_eV: PositiveFloat | None = Field(None, description="Plane-wave kinetic energy cutoff in eV.")
    name: str | None = Field(None, description="Name of the basis set (e.g., 'def2-SVP').")

class Pseudopotential(BaseModel):
    """Details of the pseudopotential or effective core potential used."""
    name: str | None = Field(None, description="Identifier for the pseudopotential")

class DispersionCorrection(BaseModel):
    """Details of the dispersion correction applied."""
    scheme: Literal[
        "DFT-D2", "DFT-D3", "DFT-D3(BJ)", "DFT-D3(ABC)", "DFT-D4", "TS", "other"
    ] = Field(description="Dispersion correction scheme.")

class DFTCodeInfo(BaseModel):
    """Information about the DFT software used."""
    name: Literal["VASP", "ORCA", "CP2K", "QuantumEspresso", "GPAW", "FHI-aims", "other"] = Field(description="Name of the DFT software package.")
    version: str | None = Field(None, description="Version string of the DFT software.")

class ConvergenceCriteria(BaseModel):
    """SCF and geometry optimization convergence criteria."""
    scf_energy_threshold: PositiveFloat | None = Field(None, description="SCF energy convergence criterion per atom in eV.")


class MethodBase(BaseModel):
    """Base class with discriminator."""
    type: str

class DFTMethod(BaseModel):
    functional: str = Field(description="Name of the DFT exchange-correlation functional.")

class DFTSettings(MethodBase):
    type: Literal["DFT"]
    code: DFTCodeInfo | None = Field(None)
    method: DFTMethod | None = Field(None)
    basis_set: BasisSet | None = None
    pseudopotential: Pseudopotential | None = None
    dispersion_correction: DispersionCorrection | None = None
    convergence_criteria: ConvergenceCriteria | None = None

class HFSettings(MethodBase):
    type: Literal["HF"]


# =============================
# === Public Dataset Loader ===
# =============================
def load_public_dataset_names() -> list[str]:
    """Load dataset names from datasets.yaml."""
    datasets_path = Path(__file__).parent / "datasets.yaml"
    with datasets_path.open() as f:
        data = yaml.safe_load(f)
    return list(data.keys())


class PublicDataset(BaseModel):
    type: Literal["public_dataset"]
    name: str = Field(
        description="Name of the public dataset.",
        json_schema_extra={"enum": load_public_dataset_names()},
    )

# ==========================
# === MLIP Specification ===
# ==========================

# Define discriminated union
MLIPData = Annotated[
    Union[DFTSettings, HFSettings, PublicDataset],
    Field(discriminator="type")
]

class MLIPSpec(BaseModel):
    """MLIP specification for DFT/HF/public dataset settings."""
    data: MLIPData


# =========================
# === Root Model Types ===
# =========================

class MLIPS(RootModel[dict[str, MLIPSpec]]):
    """Root model for MLIP specifications (model registry)."""

class Datasets(RootModel[dict[str, Union[DFTSettings, DFTSettings]]]):
    """Root model for DFT settings of public datasets."""


# ================================
# === Schema Export Entrypoint ===
# ================================

if __name__ == "__main__":
    base_path = Path(__file__).parent

    mlip_schema = MLIPS.model_json_schema()
    (base_path / "mlips-schema.json").write_text(json.dumps(mlip_schema, indent=2))

    dataset_schema = Datasets.model_json_schema()
    (base_path / "datasets-schema.json").write_text(json.dumps(dataset_schema, indent=2))
