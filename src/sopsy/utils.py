"""SOPSy utils."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from sopsy.errors import SopsyCommandFailedError
from sopsy.errors import SopsyConfigNotFoundError
from sopsy.errors import SopsyUnparsableOutpoutTypeError

DEFAULT_CONFIG_FILE = Path(".sops.yaml")


def build_config(
    config_path: Path | None, config_dict: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge config file content and python config dict."""
    config = {}
    if not config_path:
        config_path = DEFAULT_CONFIG_FILE
    config_path = find_sops_config(Path(config_path))
    config = yaml.safe_load(config_path.read_text())
    if config_dict:
        for k in config_dict:
            if k not in config:
                config[k] = config_dict[k]
            elif isinstance(config_dict[k], dict):
                config[k].update(config_dict[k])
            elif isinstance(config_dict[k], list):
                config[k].insert(0, *config_dict[k])
            else:
                config[k] = config_dict[k]
    return config


def find_sops_config(config_path: Path = DEFAULT_CONFIG_FILE) -> Path:
    """Try to find the configuration file until the filesystem root."""
    if config_path.is_absolute():
        if config_path.exists():
            return config_path
        msg = f"config path {config_path} does not exists"
        raise SopsyConfigNotFoundError(msg)

    cwd = Path.cwd()
    while True:
        cwd_config = cwd.joinpath(config_path)
        if cwd_config.exists():
            return cwd_config
        cwd_parent = cwd.parent
        if cwd == cwd_parent:
            msg = f"config path {config_path} does not exists"
            raise SopsyConfigNotFoundError(msg)
        cwd = cwd.parent


def get_dict(data: bytes | str) -> dict[str, Any]:
    """Parse data and return a dict from it."""
    out = {}

    # pyyaml can load either yaml or json content
    try:
        out = yaml.safe_load(data)
    except yaml.YAMLError as yaml_err:
        raise SopsyUnparsableOutpoutTypeError from yaml_err

    return out


def run_cmd(cmd: list[str], *, to_dict: bool) -> bytes | dict[str, Any] | None:
    """Run the given SOPS command."""
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)  # noqa: S603
    except subprocess.CalledProcessError as proc_err:
        raise SopsyCommandFailedError(proc_err.stderr.decode()) from proc_err
    if {"-i", "--in-place", "--output"}.intersection(cmd):
        return None
    if to_dict:
        return get_dict(proc.stdout)
    return proc.stdout
