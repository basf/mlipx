import typing as t

from pydantic import BaseModel, Field, PositiveFloat


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
    version: str = Field(description="Version string of the DFT software.")


class DFTMethod(BaseModel):
    """Core DFT method parameters."""

    functional: str = Field(description="Name of the exchange-correlation functional.")


class ConvergenceCriteria(BaseModel):
    """SCF and geometry optimization convergence criteria."""

    scf_energy_threshold: PositiveFloat | None = Field(
        None, description="SCF energy convergence criterion per atom in eV."
    )


class DFTSettings(BaseModel):
    code: DFTCodeInfo = Field(description="Information about the DFT software used.")
    method: DFTMethod = Field(description="Core DFT method parameters like functional")
    basis_set: BasisSet = Field(description="Details of the basis set.")
    pseudopotential: Pseudopotential | None = Field(
        None, description="Details of pseudopotentials, if applicable."
    )
    dispersion_correction: DispersionCorrection | None = Field(
        None, description="Dispersion correction applied."
    )
    convergence_criteria: ConvergenceCriteria | None = Field(
        None, description="Convergence criteria for the calculation."
    )
