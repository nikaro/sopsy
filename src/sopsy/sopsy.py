"""SOPSy, a Python wrapper around SOPS."""

from __future__ import annotations

import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from sopsy.errors import SopsyCommandNotFoundError
from sopsy.utils import build_config
from sopsy.utils import run_cmd


class SopsyInOutType(Enum):
    """SOPS output types."""

    BINARY = "binary"
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"

    def __str__(self) -> str:
        """Return the string used for str() calls."""
        return f"{self.value}"


class Sops:
    """SOPS file object."""

    def __init__(
        self,
        file: str | Path,
        *,
        config: str | Path | None = None,
        config_dict: dict[str, Any] | None = None,
        extract: str | None = None,
        in_place: bool = False,
        input_type: str | SopsyInOutType | None = None,
        output: str | Path | None = None,
        output_type: str | SopsyInOutType | None = None,
    ) -> None:
        """Initialize SOPS object."""
        self.file = Path(file).resolve(strict=True)
        self.global_args: list[str] = []
        if extract:
            self.global_args.extend(["--extract", extract])
        if in_place:
            self.global_args.extend(["--in-place"])
        if input_type:
            self.global_args.extend(["--input-type", str(input_type)])
        if output:
            self.global_args.extend(["--output", str(output)])
        if output_type:
            self.global_args.extend(["--output-type", str(output_type)])

        if isinstance(config, str):
            config = Path(config)
        if config_dict is None:
            config_dict = {}
        config_dict = build_config(config_path=config, config_dict=config_dict)
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
            yaml.dump(config_dict, fp)
            config_tmp = fp.name
        self.global_args.extend(["--config", config_tmp])

        if not shutil.which("sops"):
            msg = (
                "sops command not found, "
                "you may need to install it and/or add it to your PATH"
            )
            raise SopsyCommandNotFoundError(msg)

    def decrypt(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
        """Decrypt SOPS file."""
        cmd = ["sops", "--decrypt", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)

    def encrypt(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
        """Encrypt SOPS file."""
        cmd = ["sops", "--encrypt", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)

    def get(self, key: str, *, default: Any = None) -> Any:  # noqa: ANN401
        """Get a specific key from a SOPS encrypted file."""
        data = self.decrypt()
        if isinstance(data, dict):
            return data.get(key) or default
        return default

    def rotate(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
        """Rotate encryption keys and re-encrypt values from SOPS file."""
        cmd = ["sops", "--rotate", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)
