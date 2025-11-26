import lazy_loader as lazy

from ._version import __version__ as __version__
from ._version import __version_tuple__ as __version_tuple__

__getattr__, __dir__, __all__ = lazy.attach_stub(__name__, __file__)
