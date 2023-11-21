# ruff: noqa: INP001,S101,SLF001

"""SOPSy Tests."""

import shutil
import subprocess
from pathlib import Path

import pytest
import sopsy


def _mock_path_resolve(_, *, strict):  # noqa: ANN001,ANN202,ARG001
    return "secrets.yml"


def _mock_subprocess_run(*_args, **_kwargs):  # noqa: ANN002,ANN003,ANN202
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b'{"hello": "world"}'
    )


def test_to_dict_from_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _to_dict function with JSON input."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/sops")
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    result = sopsy.Sops("secrets.json")._to_dict(b'{"hello":"world"}')
    assert result == {"hello": "world"}


def test_to_dict_from_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _to_dict function with YAML input."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/sops")
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    result = sopsy.Sops("secrets.json")._to_dict(b"hello: world")
    assert result == {"hello": "world"}


def test_run_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_cmd function."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/sops")
    monkeypatch.setattr(Path, "resolve", _mock_path_resolve)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    result = sopsy.Sops("secrets.json")._run_cmd([], to_dict=True)
    assert result == {"hello": "world"}
