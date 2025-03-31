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
    """SOPS output types.

    Intend to be passed on `Sops().input_type` and `Sops().output_type`.

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


class Sops:
    """SOPS file or data object.

    Attributes:
        file: Path to the SOPS file. Can be None when working with data directly.
        global_args: The list of arguments that will be passed to the `sops` shell
            command. It can be used to customize it. Use it only if you know what you
            are doing.
    """

    def __init__(
        self,
        file: str | Path | None = None,
        *,
        binary_path: str | Path | None = None,
        config: str | Path | None = None,
        config_dict: dict[str, Any] | None = None,
        extract: str | None = None,
        in_place: bool = False,
        input_type: str | SopsyInOutType | None = None,
        output: str | Path | None = None,
        output_type: str | SopsyInOutType | None = None,
    ) -> None:
        """Initialize SOPS object.

        Examples:
            >>> from pathlib import Path
            >>> from sopsy import Sops
            >>> # With file
            >>> sops = Sops(
            >>>     binary_path="/app/bin/my_custom_sops",
            >>>     config=Path(".config/sops.yml"),
            >>>     file=Path("secrets.json"),
            >>> )
            >>> # With data
            >>> sops = Sops(
            >>>     config=Path(".config/sops.yml"),
            >>>     input_type=SopsyInOutType.JSON,
            >>> )
            >>> sops.encrypt_data('{"hello": "world"}')

        Args:
            file: Path to the SOPS file. Can be None when working with data directly.
            config: Path to a custom SOPS config file.
            config_dict: Allow to pass SOPS config as a python dict.
            extract: Extract a specific key or branch from the input document.
            in_place: Write output back to the same file instead of stdout.
            input_type: If not set, sops will use the file's extension to determine
                the type. Required when working with data directly.
            output: Save the output after encryption or decryption to the file
                specified.
            output_type: If not set, sops will use the input file's extension to
                determine the output format.
            binary_path: Path to the SOPS binary. If not defined it will search for it
                in the PATH environment variable.
        """
        self.bin: Path = Path("sops")
        self.file: Path | None = None
        if file:
            self.file = Path(file).resolve(strict=True)
        self.global_args: list[str] = []
        if binary_path:
            self.bin = Path(binary_path)
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

        if not shutil.which(self.bin):
            msg = (
                f"{self.bin} command not found, "
                "you may need to install it and/or add it to your PATH"
            )
            raise SopsyCommandNotFoundError(msg)

    def decrypt(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
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
        if not self.file:
            msg = "File path is required for decrypt(). Use decrypt_data() for data input."
            raise ValueError(
                msg
            )
        cmd = [str(self.bin), "--decrypt", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)

    def decrypt_data(
        self, data: str | bytes, *, to_dict: bool = True
    ) -> bytes | dict[str, Any] | None:
        """Decrypt SOPS data from stdin.

        Examples:
            >>> from sopsy import Sops, SopsyInOutType
            >>> sops = Sops(input_type=SopsyInOutType.JSON)
            >>> encrypted = '{"hello":"ENC[AES256_GCM,data:Fak3,iv:Fak3,tag:Fak3,type:str]"}'
            >>> sops.decrypt_data(encrypted)
            {'hello': 'world'}

        Args:
            data: The encrypted data to decrypt.
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        cmd = [str(self.bin), "--decrypt", *self.global_args]
        return run_cmd(cmd, to_dict=to_dict, input_data=data)

    def encrypt(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
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
        if not self.file:
            msg = "File path is required for encrypt(). Use encrypt_data() for data input."
            raise ValueError(
                msg
            )
        cmd = [str(self.bin), "--encrypt", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)

    def encrypt_data(
        self, data: str | bytes, *, to_dict: bool = True
    ) -> bytes | dict[str, Any] | None:
        """Encrypt SOPS data from stdin.

        Examples:
            >>> from sopsy import Sops, SopsyInOutType
            >>> sops = Sops(input_type=SopsyInOutType.JSON)
            >>> sops.encrypt_data('{"hello": "world"}')
            {'hello': 'ENC[AES256_GCM,data:tBVuX4Y=,iv:AAA=,tag:AAA=,type:str]'}

        Args:
            data: The plaintext data to encrypt.
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        cmd = [str(self.bin), "--encrypt", *self.global_args]
        return run_cmd(cmd, to_dict=to_dict, input_data=data)

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
        if not self.file:
            msg = "File path is required for get(). Use get_from_data() for data input."
            raise ValueError(
                msg
            )
        data: dict[Any, Any] = self.decrypt()  # pyright: ignore[reportAssignmentType]
        return data.get(key) or default

    def get_from_data(
        self, data: str | bytes, key: str, *, default: Any = None
    ) -> Any:  # noqa: ANN401
        """Get a specific key from encrypted data.

        Examples:
            >>> from sopsy import Sops, SopsyInOutType
            >>> sops = Sops(input_type=SopsyInOutType.JSON)
            >>> encrypted = '{"hello":"ENC[AES256_GCM,data:Fak3,iv:Fak3,tag:Fak3,type:str]"}'
            >>> sops.get_from_data(encrypted, "hello")
            'world'
            >>> sops.get_from_data(encrypted, "nonexistent", default="DefaultValue")
            'DefaultValue'

        Args:
            data: The encrypted data.
            key: The key to fetch in the data content.
            default: A default value in case the key does not exist or is empty.

        Returns:
            The value of the given key, or the default value.
        """
        data_dict: dict[Any, Any] = self.decrypt_data(data)  # pyright: ignore[reportAssignmentType]
        return data_dict.get(key) or default

    def rotate(self, *, to_dict: bool = True) -> bytes | dict[str, Any] | None:
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
        if not self.file:
            msg = "File path is required for rotate(). Use rotate_data() for data input."
            raise ValueError(
                msg
            )
        cmd = [str(self.bin), "--rotate", *self.global_args, str(self.file)]
        return run_cmd(cmd, to_dict=to_dict)

    def rotate_data(
        self, data: str | bytes, *, to_dict: bool = True
    ) -> bytes | dict[str, Any] | None:
        """Rotate encryption keys for data from stdin.

        Examples:
            >>> from sopsy import Sops, SopsyInOutType
            >>> sops = Sops(input_type=SopsyInOutType.JSON)
            >>> encrypted = '{"hello":"ENC[AES256_GCM,data:Fak3,iv:Fak3,tag:Fak3,type:str]"}'
            >>> sops.rotate_data(encrypted)

        Args:
            data: The encrypted data to rotate keys for.
            to_dict: Return the output as a Python dict.

        Returns:
            The output of the sops command.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        cmd = [str(self.bin), "--rotate", *self.global_args]
        return run_cmd(cmd, to_dict=to_dict, input_data=data)
