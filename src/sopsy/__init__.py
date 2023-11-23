"""SOPSy, a Python wrapper around SOPS."""

from __future__ import annotations

import json
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path
from typing import Any, Self, TypeAlias

try:
    import yaml
except ImportError:
    _has_yaml = False
else:
    _has_yaml = True

SopsyCmdOutput: TypeAlias = bytes | dict[str, Any] | None


class SopsyInOutType(StrEnum):
    """SOPS output types."""

    BINARY = "binary"
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"


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

    def __init__(  # noqa: PLR0913
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
            self.global_args.extend(["--input-type", input_type])
        if output:
            self.global_args.extend(["--output", output])
        if output_type:
            self.global_args.extend(["--output-type", output_type])
        if not shutil.which("sops"):
            raise SopsyCommandNotFoundError

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

    def _run_cmd(self: Self, cmd: list[str], *, to_dict: bool) -> SopsyCmdOutput:
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

    def decrypt(self: Self, *, to_dict: bool = True) -> SopsyCmdOutput:
        """Decrypt SOPS file."""
        cmd = ["sops", "--decrypt", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)

    def encrypt(self: Self, *, to_dict: bool = True) -> SopsyCmdOutput:
        """Encrypt SOPS file."""
        cmd = ["sops", "--encrypt", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)

    def rotate(self: Self, *, to_dict: bool = True) -> SopsyCmdOutput:
        """Rotate encryption keys and re-encrypt values from SOPS file."""
        cmd = ["sops", "--rotate", *self.global_args, str(self.file)]
        return self._run_cmd(cmd, to_dict=to_dict)
