# SOPSy

SOPSy is a simple Python wrapper arround [SOPS](https://github.com/getsops/sops).

## Installation

```sh
pip install sopsy
```

## Usage

### Retrieve a secret value

```python
from sopsy import Sops

secrets = Sops("secrets.yml").decrypt()
my_secret_key = secrets.get("my_secret_key")

print(my_secret_key)
```

### Encrypt a file

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
