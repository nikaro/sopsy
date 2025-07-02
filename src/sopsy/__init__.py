"""SOPSy, a Python wrapper around SOPS.

SOPS binary must be installed and available in your `$PATH`.
"""

from sopsy.errors import SopsyCommandFailedError
from sopsy.errors import SopsyCommandNotFoundError
from sopsy.errors import SopsyConfigNotFoundError
from sopsy.errors import SopsyError
from sopsy.errors import SopsyUnparsableOutpoutTypeError
from sopsy.sopsy import Sops
from sopsy.sopsy import SopsyInOutType

__all__ = [
    "Sops",
    "SopsyCommandFailedError",
    "SopsyCommandNotFoundError",
    "SopsyConfigNotFoundError",
    "SopsyError",
    "SopsyInOutType",
    "SopsyUnparsableOutpoutTypeError",
]
