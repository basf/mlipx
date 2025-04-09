import dataclasses
import os
from pathlib import Path

from ase.calculators.orca import ORCA, OrcaProfile


@dataclasses.dataclass
class OrcaSinglePoint:
    """Use ORCA to perform a single point calculation.

    Parameters
    ----------
    orcasimpleinput : str
        ORCA input string.
        You can use something like "PBE def2-TZVP TightSCF EnGrad".
    orcablocks : str
        ORCA input blocks.
        You can use something like "%pal nprocs 8 end".
    orca_shell : str, optional
        Path to the ORCA executable.
        The environment variable MLIPX_ORCA will be used if not provided.
    """

    orcasimpleinput: str
    orcablocks: str
    orca_shell: str | None = None

    def get_calculator(self, directory: str | Path) -> ORCA:
        profile = OrcaProfile(command=self.orca_shell or os.environ["MLIPX_ORCA"])

        calc = ORCA(
            profile=profile,
            orcasimpleinput=self.orcasimpleinput,
            orcablocks=self.orcablocks,
            directory=directory,
        )
        return calc

    @property
    def available(self) -> None:
        return None
