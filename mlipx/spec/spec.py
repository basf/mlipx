import json
import logging
from pathlib import Path
from typing import Annotated, Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, RootModel

log = logging.getLogger(__name__)
# ====================
# === Common Types ===
# ====================


class MetaData(BaseModel):
    """Metadata for the entry."""

    doi: str | None = Field(None, description="DOI of the publication, if available.")
    url: str | None = Field(None, description="URL to the publication, if available.")
    description: str | None = Field(None, description="Short description of the entry.")


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: MetaData | None = Field(None, description="Metadata for this entry.")


class BasisSet(StrictBaseModel):
    """Details of the basis set used."""

    type: Literal["plane-wave", "gaussian"] = Field(description="Type of basis set.")
    plane_wave_cutoff_eV: PositiveFloat | None = Field(
        None, description="Plane-wave kinetic energy cutoff in eV."
    )
    name: str | None = Field(
        None, description="Name of the basis set (e.g., 'def2-SVP')."
    )


class Pseudopotential(StrictBaseModel):
    """Details of the pseudopotential or effective core potential used."""

    name: str | None = Field(None, description="Identifier for the pseudopotential")


class DispersionCorrection(StrictBaseModel):
    """Details of the dispersion correction applied."""

    type: Literal[
        "DFT-D2", "DFT-D3", "DFT-D3(BJ)", "DFT-D3(ABC)", "DFT-D4", "TS", "other"
    ] = Field(description="Dispersion correction type.")


class ConvergenceCriteria(StrictBaseModel):
    """SCF and geometry optimization convergence criteria."""

    scf_energy_threshold: PositiveFloat | None = Field(
        None, description="SCF energy convergence criterion per atom in eV."
    )


class DFTMethod(StrictBaseModel):
    functional: str | Literal["PBE", "rPBE", "PBEsol", "PBE+U"] = Field(
        description="Name of the DFT exchange-correlation functional."
    )


# ==========================
# === Method Base Types ===
# ==========================


class MethodBase(StrictBaseModel):
    type: str


class HFSettings(MethodBase):
    type: Literal["HF"]


class DFTSettingsBase(MethodBase):
    type: Literal["DFT"]
    code_version: str | None = Field(None, description="Version of the DFT code used.")
    method: DFTMethod | None = Field(None)
    basis_set: BasisSet | None = None
    pseudopotential: Pseudopotential | None = None
    dispersion_correction: DispersionCorrection | None = None
    convergence_criteria: ConvergenceCriteria | None = None
    spin_polarized: bool = Field(
        False, description="Whether the calculation is spin-polarized."
    )


class VASPSettings(DFTSettingsBase):
    code: Literal["VASP"]
    # example for the future to add code-specific extensions


class GenericDFTSettings(DFTSettingsBase):
    code: Literal[
        "ORCA", "CP2K", "QuantumEspresso", "GPAW", "FHI-aims", "PSI4", "other"
    ]


# Discriminated union by `code`
DFTSettings = Annotated[
    Union[VASPSettings, GenericDFTSettings],
    Field(discriminator="code"),
]


# =============================
# === Public Dataset Loader ===
# =============================


def load_dataset_names() -> list:
    """Load dataset names from datasets.yaml."""
    datasets_path = Path(__file__).parent / "datasets.yaml"
    with datasets_path.open() as f:
        data = yaml.safe_load(f)
    return list(data.keys())


class DatasetInfo(StrictBaseModel):
    type: Literal["dataset"]
    name: str | list[str] = Field(
        description="Name of the dataset.",
        json_schema_extra={
            "anyOf": [
                {"type": "string", "enum": load_dataset_names()},
                {
                    "type": "array",
                    "items": {"type": "string", "enum": load_dataset_names()},
                },
            ]
        },
    )


# ==========================
# === MLIP Specification ===
# ==========================

MLIPData = Annotated[
    Union[DFTSettings, HFSettings, DatasetInfo],
    Field(discriminator="type"),
]


class MLIPSpec(StrictBaseModel):
    """MLIP specification for DFT/HF/public dataset settings."""

    data: MLIPData

    def resolve_datasets(self) -> "MLIPSpec":
        """Resolve dataset names to DatasetInfo."""
        if isinstance(self.data, DatasetInfo):
            datasets_path = Path(__file__).parent / "datasets.yaml"
            with datasets_path.open() as f:
                all_datasets_raw = yaml.safe_load(f)

            all_datasets = Datasets.model_validate(all_datasets_raw)
            names = self.data.name
            if isinstance(names, list):
                log.info(f"Multiple dataset names found: {names}. Using {names[0]}.")
                names = names[0]
            if names in all_datasets.root:
                dataset_spec = all_datasets.root[names]
                self.data = dataset_spec
            else:
                raise ValueError(f"Dataset '{names}' not found in datasets.yaml.")
        return self


# =========================
# === Root Model Types ===
# =========================


class MLIPS(RootModel[dict[str, MLIPSpec]]):
    """Root model for MLIP specifications (model registry)."""


class Datasets(RootModel[dict[str, Union[DFTSettings, HFSettings]]]):
    """Root model for DFT settings of public datasets."""


# ================================
# === Schema Export Entrypoint ===
# ================================

if __name__ == "__main__":
    base_path = Path(__file__).parent

    mlip_schema = MLIPS.model_json_schema()
    (base_path / "mlips-schema.json").write_text(json.dumps(mlip_schema, indent=2))

    dataset_schema = Datasets.model_json_schema()
    (base_path / "datasets-schema.json").write_text(
        json.dumps(dataset_schema, indent=2)
    )
