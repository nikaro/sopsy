> [!IMPORTANT]  
> The project has moved to SourceHut: https://sr.ht/~nka/sopsy/

# SOPSy

[![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fgithub.com%2Fnikaro%2Fsopsy%2Fraw%2Fmain%2Fpyproject.toml)](https://www.python.org/downloads/)
[![PyPI - Version](https://img.shields.io/pypi/v/sopsy)](https://pypi.org/project/sopsy/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sopsy)](https://pypi.org/project/sopsy/#files)
[![build](https://github.com/nikaro/sopsy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nikaro/sopsy/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/nikaro/sopsy/graph/badge.svg?token=DEVPQ8M6C4)](https://codecov.io/github/nikaro/sopsy)
[![Ceasefire Now](https://badge.techforpalestine.org/default)](https://techforpalestine.org/learn-more)

SOPSy is a simple Python wrapper arround [SOPS](https://github.com/getsops/sops).

## Installation

SOPS binary must be installed and available in your `$PATH`:

```sh
# use your package manager to install it
brew install sops
```

Install the SOPSy library:

```sh
pip install sopsy

# or with whatever your package/project manager is
uv add sopsy
```

## Quickstart

Retrieve a secret value:

```python
from sopsy import Sops

sops = Sops("secrets.yml")

my_secret_key = sops.get("my_secret_key")
print(f"single secret: {my_secret_key}")

secrets = sops.decrypt()
print(f"all my secrets: {secrets}")
```

Encrypt a file:

```python
import json
from pathlib import Path
from sopsy import Sops

plaintext_content = json.dumps({"hello": "world"})
Path("secrets.json").write_text(plaintext_content)

s = Sops("secrets.json", in_place=True)
# you either need a `.sops.yml` configuration file with `creation_rules` set
# or append some arguments to the `Sops.global_args` attribute:
# s.global_args.extend([
#     "--age", "age1yt3tfqlfrwdwx0z0ynwplcr6qxcxfaqycuprpmy89nr83ltx74tqdpszlw"
# ])
s.encrypt()
```

## API Reference

Check [documentation](http://sopsy.nikaro.net/reference/).
