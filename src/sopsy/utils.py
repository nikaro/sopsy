"""SOPSy utils."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import yaml

from sopsy.errors import SopsyCommandFailedError
from sopsy.errors import SopsyConfigNotFoundError
from sopsy.errors import SopsyUnparsableOutpoutTypeError

DEFAULT_CONFIG_FILE = Path(".sops.yaml")
logger = logging.getLogger(__name__)


def build_config(
    config_path: Path | None, config_dict: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge config file content and python config dict."""
    config: dict[str, Any] = {}
    if not config_path:
        config_path = DEFAULT_CONFIG_FILE
    config_path = find_sops_config(Path(config_path))
    if config_path:
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
    logger.debug("config: %s", config)
    return config


def find_sops_config(config_path: Path = DEFAULT_CONFIG_FILE) -> Path | None:
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
            msg = f"config file does not exists '{config_path}'"
            if config_path == DEFAULT_CONFIG_FILE:
                # do not fail on default config file absence
                logger.warning("default %s", msg)
                return None
            raise SopsyConfigNotFoundError(msg)
        cwd = cwd.parent


def get_dict(data: bytes | str) -> dict[str, Any]:
    """Parse data and return a dict from it."""
    out = {}

    if isinstance(data, bytes):
        data = data.decode()

    if data.startswith("{"):
        try:
            out = json.loads(data)
        except json.JSONDecodeError as json_err:
            raise SopsyUnparsableOutpoutTypeError from json_err
    else:
        try:
            out = yaml.safe_load(data)
        except yaml.YAMLError as yaml_err:
            raise SopsyUnparsableOutpoutTypeError from yaml_err

    return out


def run_cmd(
    cmd: list[str], *, to_dict: bool, input_data: str | bytes | None = None
) -> str | bytes | dict[str, Any] | None:
    """Run the given SOPS command."""
    try:
        logger.debug("run_cmd: %s", cmd)
        logger.debug("to_dict: %s", to_dict)
        logger.debug("input_data: %s", input_data)
        proc = subprocess.run(  # noqa: S603
            cmd,
            input=input_data,
            text=isinstance(input_data, str),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as proc_err:
        msg = proc_err.stderr
        if isinstance(msg, bytes):
            msg = msg.decode()
        raise SopsyCommandFailedError(msg) from proc_err
    if {"-i", "--in-place", "--output"}.intersection(cmd):
        return None
    if to_dict:
        return get_dict(proc.stdout)
    return proc.stdout
