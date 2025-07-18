"""SOPSy, a Python wrapper around SOPS."""

from __future__ import annotations

import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from sopsy.errors import SopsyCommandNotFoundError
from sopsy.errors import SopsyError
from sopsy.utils import build_config
from sopsy.utils import run_cmd


class SopsyInOutType(Enum):
    """SOPS output types.

    Intended to be passed on `Sops().input_type` and `Sops().output_type`.

    Attributes:
        BINARY (str): Binary type.
        DOTENV (str): DotEnv type.
        JSON (str): JSON type.
        YAML (str): YAML type.
    """

    BINARY = "binary"
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"

    def __str__(self) -> str:
        """Return the string used for str() calls."""
        return f"{self.value}"


class SopsyInputSource(Enum):
    """SOPS input source.

    Used to determinie wether input data come from a file or stdin.

    Attributes:
        FILE (str): From an on-disk file.
        STDIN (str): From stdin.
    """

    FILE = "file"
    STDIN = "stdin"


class Sops:
    """SOPS file object.

    Attributes:
        bin: Path to the SOPS binary.
        file: Path to the SOPS file or content to encrypt/decrypt.
        global_args: The list of arguments that will be passed to the `sops` shell
            command. It can be used to customize it. Use it only if you know what you
            are doing.
        input_source: Wether input data come from a file or stdin.
    """

    def __init__(  # noqa: C901
        self,
        file: str | Path | bytes,
        *,
        binary_path: str | Path | None = None,
        config: str | Path | None = None,
        config_dict: dict[str, Any] | None = None,
        extract: str | None = None,
        in_place: bool = False,
        input_type: str | SopsyInOutType | None = None,
        output: str | Path | None = None,
        output_type: str | SopsyInOutType | None = None,
        input_source: SopsyInputSource = SopsyInputSource.FILE,
    ) -> None:
        """Initialize SOPS object.

        Examples:
            >>> from pathlib import Path
            >>> from sopsy import Sops
            >>> sops = Sops(
            >>>     binary_path="/app/bin/my_custom_sops",
            >>>     config=Path(".config/sops.yml"),
            >>>     file=Path("secrets.json"),
            >>> )

        Args:
            file: Path to the SOPS file or content to encrypt/decrypt.
            config: Path to a custom SOPS config file.
            config_dict: Allow to pass SOPS config as a python dict.
            extract: Extract a specific key or branch from the input document.
            in_place: Write output back to the same file instead of stdout.
            input_type: If not set, sops will use the file's extension to determine
                the type.
            output: Save the output after encryption or decryption to the file
                specified.
            output_type: If not set, sops will use the input file's extension to
                determine the output format.
            binary_path: Path to the SOPS binary. If not defined it will search for it
                in the PATH environment variable.
            input_source: Wether input data come from a file or stdin.
        """
        self.bin: Path = Path(binary_path) if binary_path else Path("sops")
        self.file: str | Path | bytes = file
        self.global_args: list[str] = []
        self.input_source: SopsyInputSource = input_source
        if extract:
            self.global_args.extend(["--extract", extract])
        if in_place:
            self.global_args.extend(["--in-place"])
        if input_type:
            self.global_args.extend(["--input-type", str(input_type)])
            self.input_type: str | SopsyInOutType | None = input_type
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
        self.config: list[str] = ["--config", config_tmp]

        if input_source == SopsyInputSource.STDIN and not input_type:
            msg = "When using stdin source, input MUST be specified"
            raise SopsyError(msg)

        if input_source == SopsyInputSource.STDIN and isinstance(file, Path):
            msg = "Path type cannot be used with stdin input source."
            raise SopsyError(msg)

        if not shutil.which(self.bin):
            msg = (
                f"{self.bin} command not found, "
                "you may need to install it and/or add it to your PATH"
            )
            raise SopsyCommandNotFoundError(msg)

    def decrypt(self, *, to_dict: bool = True) -> str | bytes | dict[str, Any] | None:
        """Decrypt SOPS file.

        Examples:
            >>> from sopsy import Sops, SopsyInOutType
            >>> sops = Sops("secrets.json", output_type=SopsyInOutType.YAML)
            >>> sops.decrypt(to_dict=False)
            hello: world

        Args:
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        cmd = [str(self.bin), *self.config, "decrypt", *self.global_args]
        if self.input_source == SopsyInputSource.STDIN:
            cmd.extend(["--filename-override", f"dummy.{self.input_type}"])
            input_data = self.file
            assert not isinstance(input_data, Path)  # noqa: S101
        else:
            cmd.append(str(self.file))
            input_data = None
        return run_cmd(cmd, to_dict=to_dict, input_data=input_data)

    def encrypt(self, *, to_dict: bool = True) -> str | bytes | dict[str, Any] | None:
        """Encrypt SOPS file.

        Examples:
            >>> import json
            >>> from pathlib import Path
            >>> from sopsy import Sops
            >>> secrets = Path("secrets.json")
            >>> secrets.write_text(json.dumps({"hello": "world"}))
            >>> sops = Sops(secrets, in_place=True)
            >>> sops.encrypt()

        Args:
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        cmd = [str(self.bin), *self.config, "encrypt", *self.global_args]
        if self.input_source == SopsyInputSource.STDIN:
            cmd.extend(["--filename-override", f"dummy.{self.input_type}"])
            input_data = self.file
            assert not isinstance(input_data, Path)  # noqa: S101
        else:
            cmd.append(str(self.file))
            input_data = None
        return run_cmd(cmd, to_dict=to_dict, input_data=input_data)

    def get(self, key: str, *, default: Any = None) -> Any:  # noqa: ANN401
        """Get a specific key from a SOPS encrypted file.

        Examples:
            >>> from sopsy import Sops
            >>> sops = Sops("secrets.json")
            >>> sops.get("hello")
            b'world'
            >>> sops.get("nonexistent", default="DefaultValue")
            'DefaultValue'

        Args:
            key: The key to fetch in the SOPS file content.
            default: A default value in case the key does not exist or is empty.

        Returns:
            The value of the given key, or the default value.
        """
        data: dict[Any, Any] = self.decrypt()  # type: ignore[assignment]
        return data.get(key) or default

    def rotate(self, *, to_dict: bool = True) -> str | bytes | dict[str, Any] | None:
        """Rotate encryption keys and re-encrypt values from SOPS file.

        Examples:
            >>> from sopsy import Sops
            >>> sops = Sops("secrets.json", in_place=True)
            >>> sops.rotate()

        Args:
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        cmd = [str(self.bin), *self.config, "rotate", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)
