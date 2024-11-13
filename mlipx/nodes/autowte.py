"""Automatic heat-conductivity predictions from the Wigner Transport Equation.

Based on https://github.com/MPA2suite/autoWTE

Use pip install git+https://github.com/MPA2suite/autoWTE
and conda install -c conda-forge phono3py
"""

import zntrack

from mlipx.abc import NodeWithCalculator


class AutoWTE(zntrack.Node):
    model: NodeWithCalculator = zntrack.deps()
