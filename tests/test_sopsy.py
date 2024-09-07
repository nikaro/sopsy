"""SOPSy Tests."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from typing import NoReturn

import pytest

from sopsy import errors
from sopsy import sopsy
from sopsy import utils


def test_get_dict_from_json() -> None:
    """Test utils.get_dict function with JSON input."""
    result = utils.get_dict(b'{"hello":"world"}')
    assert result == {"hello": "world"}


def test_get_dict_from_yaml() -> None:
    """Test utils.get_dict function with YAML input."""
    result = utils.get_dict(b"hello: world")
    assert result == {"hello": "world"}


def test_get_dict_bad_content(tmp_path: Path) -> None:
    """Test utils.get_dict function with unsupported input content type."""
    bad_content = "echo 'hello world'\n---\nhello: world\n"
    bad_file = tmp_path / "hello.sh"
    _ = bad_file.write_text(bad_content)
    with pytest.raises(errors.SopsyUnparsableOutpoutTypeError):
        _ = utils.get_dict(bad_file.read_bytes())


def test_run_cmd_to_inplace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test utils.run_cmd function with inplace argument."""
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    result = utils.run_cmd(["-i"], to_dict=False)
    assert result is None


def test_run_cmd_to_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test utils.run_cmd function to bytes."""
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    result = utils.run_cmd([], to_dict=False)
    assert result == b'{"hello": "world"}'


def test_run_cmd_to_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test utils.run_cmd function to dict."""
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    result = utils.run_cmd([], to_dict=True)
    assert result == {"hello": "world"}


def test_run_cmd_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test utils.run_cmd function failing."""
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run_fail)
    with pytest.raises(errors.SopsyCommandFailedError):
        _ = utils.run_cmd([], to_dict=True)


def test_find_sops_config_default(tmp_path: Path) -> None:
    """Test utils.find_sops_config function without argument."""
    os.chdir(tmp_path)
    sops_config = tmp_path / ".sops.yaml"
    _ = sops_config.write_text("hello: world")
    result = utils.find_sops_config()
    assert sops_config == result


def test_find_sops_config_default_in_parent_dir(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with default file in parent directory."""
    sops_config = tmp_path / ".sops.yaml"
    _ = sops_config.write_text("hello: world")
    sub_dir = tmp_path / "hello_world"
    sub_dir.mkdir()
    os.chdir(sub_dir)
    result = utils.find_sops_config()
    assert sops_config == result


def test_find_sops_config_custom_absolute(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with custom filename."""
    os.chdir(tmp_path)
    custom_filename = Path("hello.yml")
    sops_config = tmp_path / custom_filename
    _ = sops_config.write_text("hello: world")
    result = utils.find_sops_config(config_path=custom_filename)
    assert sops_config == result


def test_find_sops_config_custom_relative(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with custom filename."""
    os.chdir(tmp_path)
    custom_filename = Path("hello.yml")
    sops_config = tmp_path / custom_filename
    _ = sops_config.write_text("hello: world")
    result = utils.find_sops_config(config_path=custom_filename)
    assert sops_config == result


def test_find_sops_config_custom_in_sub_dir_absolute(tmp_path: Path) -> None:
    """Test utils.find_sops_config function in sub directory."""
    os.chdir(tmp_path)
    sub_dir = tmp_path / "hello_world"
    sub_dir.mkdir()
    sops_config = sub_dir / ".sops.yaml"
    _ = sops_config.write_text("hello: world")
    result = utils.find_sops_config(config_path=sops_config)
    assert sops_config == result


def test_find_sops_config_custom_in_sub_dir_relative(tmp_path: Path) -> None:
    """Test utils.find_sops_config function in sub directory."""
    os.chdir(tmp_path)
    sub_dir = tmp_path / "hello_world"
    sub_dir.mkdir()
    sops_config = sub_dir / ".sops.yaml"
    _ = sops_config.write_text("hello: world")
    result = utils.find_sops_config(config_path=sops_config.relative_to(tmp_path))
    assert sops_config == result


def test_find_sops_config_default_nonexistent(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with non existent default file."""
    os.chdir(tmp_path)
    with pytest.raises(errors.SopsyConfigNotFoundError):
        _ = utils.find_sops_config()


def test_find_sops_config_custom_relative_nonexistent(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with non existent relative custom file."""
    nonexistent = tmp_path / "hello.yml"
    with pytest.raises(errors.SopsyConfigNotFoundError):
        _ = utils.find_sops_config(nonexistent.relative_to(tmp_path))


def test_find_sops_config_custom_absolute_nonexistent(tmp_path: Path) -> None:
    """Test utils.find_sops_config function with non existent relative custom file."""
    nonexistent = tmp_path / "hello.yml"
    with pytest.raises(errors.SopsyConfigNotFoundError):
        _ = utils.find_sops_config(nonexistent)


def test_build_config(tmp_path: Path) -> None:
    """Test utils.build_config."""
    os.chdir(tmp_path)
    sops_config = tmp_path / ".sops.yaml"
    _ = sops_config.write_text(
        "key1: [world]\nkey2: {subkey1: hello}\nerase_me: please"
    )
    result = utils.build_config(
        config_path=None,
        config_dict={
            "key1": ["pytest"],
            "key2": {"subkey2": "world"},
            "newkey": "hello",
            "erase_me": "ok",
        },
    )
    assert result == {
        "key1": ["pytest", "world"],
        "key2": {"subkey1": "hello", "subkey2": "world"},
        "newkey": "hello",
        "erase_me": "ok",
    }


def test_sops_init(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    s = sopsy.Sops(sops_file)
    assert s.file == sops_file


def test_sops_init_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with config arg."""
    sops_config = tmp_path / "config.yml"
    _ = sops_config.write_text("config: value")
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    _ = sopsy.Sops(
        sops_file,
        config=str(sops_config),
    )


def test_sops_init_extract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with extract arg."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    s = sopsy.Sops(
        sops_file,
        extract='["hello"]',
    )
    assert "--extract" in s.global_args


def test_sops_init_inplace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with in_place arg."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    s = sopsy.Sops(
        sops_file,
        in_place=True,
    )
    d = s.decrypt()
    assert "--in-place" in s.global_args
    assert d is None


def test_sops_init_inputtype(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with input_type arg."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    s = sopsy.Sops(
        sops_file,
        input_type=sopsy.SopsyInOutType.JSON,
    )
    assert "--input-type" in s.global_args
    assert "json" in s.global_args


def test_sops_init_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with output arg."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    s = sopsy.Sops(
        sops_file,
        output=Path("plain.json"),
    )
    d = s.decrypt()
    assert "--output" in s.global_args
    assert d is None


def test_sops_init_outputtype(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function with output_type arg."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    s = sopsy.Sops(
        sops_file,
        output_type=sopsy.SopsyInOutType.YAML,
    )
    assert "--output-type" in s.global_args
    assert "yaml" in s.global_args


def test_sops_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.__init__ function command not found."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _not_return_sops_path)
    with pytest.raises(errors.SopsyCommandNotFoundError):
        _ = sopsy.Sops(sops_file)


def test_sops_decrypt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.decrypt function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    d = sopsy.Sops(sops_file).decrypt()
    assert isinstance(d, dict)
    assert d == {"hello": "world"}


def test_sops_encrypt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.encrypt function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    e = sopsy.Sops(sops_file).encrypt()
    assert isinstance(e, dict)
    assert e == {"hello": "world"}


def test_sops_rotate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.rotate function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    r = sopsy.Sops(sops_file).rotate()
    assert isinstance(r, dict)
    assert r == {"hello": "world"}


def test_sops_get(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.get function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    g = sopsy.Sops(sops_file).get("hello")
    assert isinstance(g, str)
    assert g == "world"


def test_sops_get_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.get function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    g = sopsy.Sops(sops_file).get("nonexistent")
    assert g is None


def test_sops_get_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test sops.Sops.get function."""
    sops_file = tmp_path / "secret.json"
    _ = sops_file.write_text('{"hello":"world"}')
    monkeypatch.setattr(shutil, "which", _return_sops_path)
    monkeypatch.setattr(subprocess, "run", _mock_subprocess_run)
    g = sopsy.Sops(sops_file).get("nonexistent", default="hello")
    assert isinstance(g, str)
    assert g == "hello"


def _return_sops_path(*_args: Any, **_kwargs: Any) -> str:
    return "/usr/bin/sops"


def _not_return_sops_path(*_args: Any, **_kwargs: Any) -> None:
    return None


def _mock_subprocess_run(*_args: Any, **_kwargs: Any) -> object:
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b'{"hello": "world"}'
    )


def _mock_subprocess_run_fail(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise subprocess.CalledProcessError(cmd=[], returncode=1, stderr=b"pytest")
