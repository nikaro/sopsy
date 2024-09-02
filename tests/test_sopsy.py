"""SOPSy Tests."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

import sopsy


def _mock_path_resolve(*_args: Any, **_kwargs: Any) -> str:
    return "secrets.yml"


def _mock_subprocess_run(*_args: Any, **_kwargs: Any) -> object:
    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=b'{"hello": "world"}',
    )


def _return_sops_path(*_args: Any, **_kwargs: Any) -> str:
    return "/usr/bin/sops"


def test_to_dict_from_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _to_dict function with JSON input."""
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    result = sopsy.Sops(Path("secrets.json"))._to_dict(b'{"hello":"world"}')  # pyright: ignore[reportPrivateUsage]
    assert result == {"hello": "world"}


def test_to_dict_from_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _to_dict function with YAML input."""
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    result = sopsy.Sops("secrets.json")._to_dict(b"hello: world")  # pyright: ignore[reportPrivateUsage]
    assert result == {"hello": "world"}


def test_run_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_cmd function."""
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    result = sopsy.Sops("secrets.json")._run_cmd([], to_dict=True)  # pyright: ignore[reportPrivateUsage]
    assert result == {"hello": "world"}
