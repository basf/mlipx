import dataclasses
import warnings

import ase
import numpy as np

from mlipx.abc import DynamicsObserver


@dataclasses.dataclass
class MaximumForceObserver(DynamicsObserver):
    """Evaluate if the maximum force on a single atom exceeds a threshold.

    Parameters
    ----------
    f_max : float
        Maximum allowed force norm on a single atom


    Example
    -------

    >>> import zntrack, mlipx
    >>> project = zntrack.Project()
    >>> observer = mlipx.MaximumForceObserver(f_max=0.1)
    >>> with project:
    ...     md = mlipx.MolecularDynamics(
    ...         observers=[observer],
    ...         **kwargs
    ...     )
    >>> project.build()
    """

    f_max: float

    def check(self, atoms: ase.Atoms) -> bool:
        """Check if the maximum force on a single atom exceeds the threshold.

        Parameters
        ----------
        atoms : ase.Atoms
            Atoms object to evaluate
        """

        max_force = np.linalg.norm(atoms.get_forces(), axis=1).max()
        if max_force > self.f_max:
            warnings.warn(f"Maximum force {max_force} exceeds {self.f_max}")
            return True
        return False
