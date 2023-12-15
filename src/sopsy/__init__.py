"""SOPSy, a Python wrapper around SOPS."""

from __future__ import annotations

import json
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import overload

if TYPE_CHECKING:
    from typing_extensions import Self

try:
    import yaml
except ImportError:
    _has_yaml = False
else:
    _has_yaml = True


class SopsyInOutType(Enum):
    """SOPS output types."""

    BINARY = "binary"
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"

    def __str__(self: Self) -> str:
        """Return the string used for str() calls."""
        return f"{self.value}"


class SopsyError(Exception):
    """Sopsy base exception class."""


class SopsyUnparsableOutpoutTypeError(SopsyError):
    """Sopsy could not read SOPS output content."""


class SopsyCommandNotFoundError(SopsyError):
    """Sopsy could not find SOPS command in PATH."""


class SopsyCommandFailedError(SopsyError):
    """Sopsy could not execute SOPS command successfully."""


class Sops:
    """SOPS file object."""

    def __init__(
        self: Self,
        file: str,
        *,
        config: str | None = None,
        extract: str | None = None,
        in_place: bool | None = None,
        input_type: SopsyInOutType | str | None = None,
        output: str | None = None,
        output_type: SopsyInOutType | str | None = SopsyInOutType.JSON,
    ) -> None:
        """Initialize SOPS object."""
        self.file = Path(file).resolve(strict=True)
        self.global_args = []
        if config:
            config = str(Path(config).resolve(strict=True))
            self.global_args.extend(["--config", config])
        if extract:
            self.global_args.extend(["--extract", extract])
        if in_place:
            self.global_args.extend(["--in-place"])
        if input_type:
            self.global_args.extend(["--input-type", str(input_type)])
        if output:
            self.global_args.extend(["--output", output])
        if output_type:
            self.global_args.extend(["--output-type", str(output_type)])
        if not shutil.which("sops"):
            msg = (
                "sops command not found, "
                "you may need to install it and/or add it to your PATH"
            )
            raise SopsyCommandNotFoundError(msg)

    def _to_dict(self: Self, data: bytes) -> dict[str, Any]:
        """Parse data and return a dict from it."""
        out = {}
        err: Exception | None = None

        try:
            out = json.loads(data)
        except json.JSONDecodeError as json_err:
            err = json_err

        if _has_yaml:
            try:
                out = yaml.safe_load(data)
            except yaml.YAMLError as yaml_err:
                err = yaml_err

        if not out:
            raise SopsyUnparsableOutpoutTypeError from err

        return out

    def _run_cmd(
        self: Self,
        cmd: list[str],
        *,
        to_dict: bool,
    ) -> bytes | dict[str, Any] | None:
        """Run the given SOPS command."""
        try:
            proc = subprocess.run(cmd, capture_output=True, check=True)  # noqa: S603
        except subprocess.CalledProcessError as err:
            raise SopsyCommandFailedError(err.stderr.decode()) from err
        if {"-i", "--in-place", "--output"}.intersection(self.global_args):
            return None
        if to_dict:
            return self._to_dict(proc.stdout)
        return proc.stdout

    @overload
    def decrypt(self: Self, *, to_dict: Literal[True] = True) -> dict[str, Any] | None:
        ...

    @overload
    def decrypt(self: Self, *, to_dict: Literal[False]) -> bytes | None:
        ...

    def decrypt(self: Self, *, to_dict: bool = True) -> dict[str, Any] | bytes | None:
        """Decrypt SOPS file."""
        cmd = ["sops", "--decrypt", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)

    @overload
    def encrypt(self: Self, *, to_dict: Literal[True] = True) -> dict[str, Any] | None:
        ...

    @overload
    def encrypt(self: Self, *, to_dict: Literal[False]) -> bytes | None:
        ...

    def encrypt(self: Self, *, to_dict: bool = True) -> dict[str, Any] | bytes | None:
        """Encrypt SOPS file."""
        cmd = ["sops", "--encrypt", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)

    def get(
        self: Self,
        key: str,
        *,
        default: dict[str, Any] | str | None = None,
    ) -> dict[str, Any] | str | None:
        """Get a specific key from a SOPS encrypted file."""
        data = self.decrypt()
        if isinstance(data, dict):
            return data.get(key) or default
        return default

    @overload
    def rotate(self: Self, *, to_dict: Literal[True] = True) -> dict[str, Any] | None:
        ...

    @overload
    def rotate(self: Self, *, to_dict: Literal[False]) -> bytes | None:
        ...

    def rotate(self: Self, *, to_dict: bool = True) -> dict[str, Any] | bytes | None:
        """Rotate encryption keys and re-encrypt values from SOPS file."""
        cmd = ["sops", "--rotate", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)
