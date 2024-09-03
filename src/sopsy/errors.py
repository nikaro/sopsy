"""SOPSy Exceptions."""


class SopsyError(Exception):
    """Sopsy base exception class."""


class SopsyUnparsableOutpoutTypeError(SopsyError):
    """Sopsy could not read SOPS output content."""


class SopsyCommandNotFoundError(SopsyError):
    """Sopsy could not find SOPS command in PATH."""


class SopsyCommandFailedError(SopsyError):
    """Sopsy could not execute SOPS command successfully."""


class SopsyConfigNotFoundError(SopsyError):
    """Sopsy could not find the given configuration file."""
