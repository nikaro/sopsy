# Usage

## Installation

SOPS binary should be installed and available in your `$PATH`:

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
