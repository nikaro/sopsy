"""SOPSy, a Python wrapper around SOPS."""

from sopsy.errors import SopsyCommandFailedError
from sopsy.errors import SopsyCommandNotFoundError
from sopsy.errors import SopsyConfigNotFoundError
from sopsy.errors import SopsyError
from sopsy.errors import SopsyUnparsableOutpoutTypeError
from sopsy.sopsy import Sops

__all__ = [
    "SopsyCommandFailedError",
    "SopsyCommandNotFoundError",
    "SopsyConfigNotFoundError",
    "SopsyError",
    "SopsyUnparsableOutpoutTypeError",
    "Sops",
]
