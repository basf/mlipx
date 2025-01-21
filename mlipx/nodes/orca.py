import dataclasses
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
    orca_shell : str
        Path to the ORCA executable.
    """

    orca_shell: str
    orcasimpleinput: str
    orcablocks: str

    def get_calculator(self, directory: str | Path) -> ORCA:
        profile = OrcaProfile(command=self.orca_shell)

        calc = ORCA(
            profile=profile,
            orcasimpleinput=self.orcasimpleinput,
            orcablocks=self.orcablocks,
            directory=directory,
        )
        return calc
