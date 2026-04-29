# confp Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize confp from 0.4.1 to 1.0.0 — modern packaging (pyproject.toml + uv), drop Python 2 compat, remove runtime auto-install.

**Architecture:** Replace legacy packaging files with a single `pyproject.toml`. Clean up all Python 2 compatibility code. Replace the runtime `install_missing_requirements()` system with packaging extras (`confp[redis]`, etc.) and clear `ImportError` messages.

**Tech Stack:** Python 3.10+, uv, hatchling, jinja2, pyyaml, cerberus

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `pyproject.toml` | Create | All packaging config, deps, extras, metadata |
| `setup.cfg` | Modify | bamp config only — update version + files list |
| `setup.py` | Delete | Replaced by pyproject.toml |
| `Pipfile` | Delete | Replaced by uv |
| `Pipfile.lock` | Delete | Replaced by uv.lock |
| `src/confp/__main__.py` | Modify | Remove `__future__` import, remove `install_missing_requirements` import/call |
| `src/confp/backends/__init__.py` | Modify | Remove `install_missing_requirements()`, Py2 cruft, modernize ABC |
| `src/confp/backends/redis.py` | Modify | Remove `__future__`, `REQUIREMENTS`, add ImportError handling |
| `src/confp/backends/etcd.py` | Modify | Same as redis.py |
| `src/confp/backends/terraform_s3.py` | Modify | Same as redis.py |
| `src/confp/exceptions.py` | Modify | Remove `CannotInstallModuleRequirements` |
| `Dockerfile` | Modify | Rebase image, use uv |

---

### Task 1: Create pyproject.toml and delete legacy packaging files

**Files:**
- Create: `pyproject.toml`
- Delete: `setup.py`
- Delete: `Pipfile`
- Delete: `Pipfile.lock`
- Modify: `setup.cfg`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "confp"
version = "1.0.0"
description = "Configuration management using Jinja2 templates and pluggable backends"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
dependencies = [
    "jinja2",
    "pyyaml",
    "cerberus",
]

[project.optional-dependencies]
redis = ["redis"]
etcd = ["python-etcd"]
terraform = ["boto3"]

[project.scripts]
confp = "confp.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/confp"]

[dependency-groups]
dev = [
    "pytest",
]
```

- [ ] **Step 2: Update `setup.cfg`**

Replace the entire file with:

```ini
[bamp]
version = 1.0.0
files =
    setup.cfg
    pyproject.toml
vcs = git
commit = True
message = {current_version} -> {new_version}
allow_dirty = False
tag = True
tag_name = v{new_version}
```

- [ ] **Step 3: Delete `setup.py`, `Pipfile`, `Pipfile.lock`**

```bash
git rm setup.py Pipfile Pipfile.lock
```

- [ ] **Step 4: Initialize uv and generate lockfile**

```bash
uv lock
```

- [ ] **Step 5: Verify the package is installable**

```bash
uv sync --all-extras
uv run python -c "import confp; print('import ok')"
```

Expected: prints `import ok` with no errors.

- [ ] **Step 6: Run existing tests**

```bash
uv run pytest tests/ -v
```

Expected: `test_env.py` tests all pass.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml setup.cfg uv.lock
git commit -m "Replace setup.py/Pipfile with pyproject.toml + uv"
```

---

### Task 2: Remove Python 2 compat from backends/__init__.py

**Files:**
- Modify: `src/confp/backends/__init__.py`

- [ ] **Step 1: Replace the entire file**

Replace the contents of `src/confp/backends/__init__.py` with:

```python
import logging
from abc import ABC, abstractmethod

from .. import exceptions

LOG = logging.getLogger(__name__)


class BackendBase(ABC):
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_val(self, key):
        pass

    def get_all(self):
        raise exceptions.NoBackendSupport()

    def get_val_default(self, key, default):
        """
        Get a value from the backend, but fall back to the default value if
        the key doesn't exist.
        """
        try:
            return self.get_val(key)
        except exceptions.KeyNotFoundException:
            pass
        LOG.info(
            "Key %r not found in backend %r. Falling back to default value.",
            key,
            self.name,
        )
        return default
```

This removes:
- `from __future__ import print_function`
- Python 2/3 `urlparse` try/except (and the now-unused `urlparse` import)
- `BackendBase(object)` + `__metaclass__ = ABCMeta` → `BackendBase(ABC)`
- `install_missing_requirements()` function entirely
- `pkg_resources` import

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/confp/backends/__init__.py
git commit -m "Remove Python 2 compat and install_missing_requirements from backends"
```

---

### Task 3: Remove install_missing_requirements from __main__.py

**Files:**
- Modify: `src/confp/__main__.py`

- [ ] **Step 1: Edit `src/confp/__main__.py`**

Remove the `from __future__ import print_function` line at the top.

Remove `install_missing_requirements` from this import line:

```python
from .backends import install_missing_requirements
```

So the line is deleted entirely (nothing else is imported from `.backends` at module level).

Remove the call to `install_missing_requirements(backend_module)` inside `instantiate_backend()` (line 40 in the original). The function should become:

```python
def instantiate_backend(name, config):
    """
    Import the backend module and instantiate it with the provided config.
    """
    LOG.debug("Instantiating backend %r", name)
    backend_module = import_module("confp.backends.%s" % config["type"])
    config = validate_module_config(backend_module.CONFIG_SCHEMA, config)
    backend = backend_module.Backend(name, config)
    backend.connect()
    return backend
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/confp/__main__.py
git commit -m "Remove __future__ import and install_missing_requirements usage"
```

---

### Task 4: Clean up backend modules — redis, etcd, terraform_s3

**Files:**
- Modify: `src/confp/backends/redis.py`
- Modify: `src/confp/backends/etcd.py`
- Modify: `src/confp/backends/terraform_s3.py`

- [ ] **Step 1: Replace `src/confp/backends/redis.py`**

```python
import logging

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException

LOG = logging.getLogger(__name__)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update(
    {
        "host": dict(type="string", required=True, empty=False),
        "port": dict(type="integer", default=6379, min=1, max=65535),
        "db": dict(type="integer", default=0, min=0, max=15),
        "password": dict(type="string", empty=False),
        "decode_responses": dict(type="boolean", default=True),
    }
)


class Backend(BackendBase):
    def connect(self):
        try:
            from redis import StrictRedis
        except ImportError:
            raise ImportError(
                "The redis backend requires the 'redis' package. "
                "Install it with: pip install confp[redis]"
            )

        self.db = StrictRedis(
            host=self.config["host"],
            port=self.config["port"],
            db=self.config["db"],
            password=self.config.get("password"),
            decode_responses=self.config["decode_responses"],
        )

    def disconnect(self):
        LOG.debug("Disconnecting from Redis server")

    def get_val(self, key):
        LOG.debug(
            "Getting value of key %r from redis server at %s:%s",
            key,
            self.config["host"],
            self.config["port"],
        )
        var = self.db.get(key)
        if var is None:
            raise KeyNotFoundException("Key %r was not found in Redis." % key)
        return var
```

Changes: removed `from __future__ import absolute_import`, removed `REQUIREMENTS` tuple, added `ImportError` handling in `connect()`.

- [ ] **Step 2: Replace `src/confp/backends/etcd.py`**

```python
import logging

from . import BackendBase
from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException

LOG = logging.getLogger(__name__)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update(
    {
        "host": dict(type="string", required=True, empty=False),
        "port": dict(type="integer", default=2379, min=1, max=65535),
        "protocol": dict(type="string", default="https", empty=False),
    }
)


class Backend(BackendBase):
    def connect(self):
        try:
            import etcd
        except ImportError:
            raise ImportError(
                "The etcd backend requires the 'python-etcd' package. "
                "Install it with: pip install confp[etcd]"
            )

        self.etcd = etcd
        self.db = etcd.Client(
            host=self.config["host"], port=self.config["port"], protocol=self.config["protocol"]
        )

    def disconnect(self):
        LOG.debug("Disconnecting from etcd server")

    def get_val(self, key):
        LOG.debug(
            "Getting value of key %r from etcd server at %s:%s",
            key,
            self.config["host"],
            self.config["port"],
        )
        try:
            return self.db.get(key).value
        except self.etcd.EtcdKeyNotFound:
            raise KeyNotFoundException("Key %r was not found in etcd." % key)
```

Changes: removed `from __future__ import absolute_import`, removed `REQUIREMENTS` tuple, added `ImportError` handling in `connect()`.

- [ ] **Step 3: Replace `src/confp/backends/terraform_s3.py`**

```python
import json
import logging

from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException
from . import BackendBase

LOG = logging.getLogger(__name__)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update(
    {
        "bucket": dict(type="string", required=True, empty=False),
        "key": dict(type="string", required=True, empty=False),
    }
)

"""
{
    "version": 3,
    "terraform_version": "0.11.12",
    "serial": 65,
    "lineage": "89362db3-ded7-831f-fadd-63a32796ad81",
    "modules": [
        {
            "path": [
                "root"
            ],
            "outputs": {
                "app_access_key_id": {
                    "sensitive": false,
                    "type": "string",
                    "value": "AKIAIMUOVF5GYGI6Z3VQ"
                },
"""


class Backend(BackendBase):
    def connect(self):
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "The terraform_s3 backend requires the 'boto3' package. "
                "Install it with: pip install confp[terraform]"
            )

        s3 = boto3.client("s3")
        LOG.debug(
            "Getting terraform state from s3://%s/%s",
            self.config["bucket"],
            self.config["key"],
        )
        resp = s3.get_object(Bucket=self.config["bucket"], Key=self.config["key"])
        self.state_raw = json.load(resp["Body"])
        self.state_raw["modules_dict"] = {}
        self.state = {}
        for module in self.state_raw["modules"]:
            self.state_raw["modules_dict"][".".join(module["path"])] = module["outputs"]
            key = module["path"][1:]
            for name, value in module["outputs"].items():
                self.state[".".join(key + [name])] = value["value"]

    def disconnect(self):
        pass

    def get_all(self):
        return self.state_raw

    def get_val(self, key):
        try:
            return self.state[key]
        except KeyError:
            raise KeyNotFoundException("Key %r was not found in Terraform state." % key)
```

Changes: removed `from __future__ import absolute_import`, removed `REQUIREMENTS` tuple, added `ImportError` handling in `connect()`.

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/confp/backends/redis.py src/confp/backends/etcd.py src/confp/backends/terraform_s3.py
git commit -m "Clean up backend modules: remove Py2 compat, add ImportError guidance"
```

---

### Task 5: Remove CannotInstallModuleRequirements from exceptions.py

**Files:**
- Modify: `src/confp/exceptions.py`

- [ ] **Step 1: Edit `src/confp/exceptions.py`**

Remove the `CannotInstallModuleRequirements` class. The file becomes:

```python
class KeyNotFoundException(Exception):
    pass


class ConfigValidationException(Exception):
    pass


class NoBackendSupport(Exception):
    pass
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/confp/exceptions.py
git commit -m "Remove unused CannotInstallModuleRequirements exception"
```

---

### Task 6: Update Dockerfile

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Replace `Dockerfile`**

```dockerfile
FROM python:3.12-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /confp

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY README.md ./

RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "python", "-m", "confp"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "Update Dockerfile to Python 3.12 + uv"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify CLI entry point works**

```bash
uv run confp --help
```

Expected: prints argument parser usage (config_path, --loop, --template).

- [ ] **Step 3: Verify package builds**

```bash
uv build
```

Expected: produces `dist/confp-1.0.0.tar.gz` and `dist/confp-1.0.0-py3-none-any.whl`.

- [ ] **Step 4: Check no leftover references to removed code**

```bash
grep -r "install_missing_requirements\|REQUIREMENTS\|pkg_resources\|from __future__\|CannotInstallModuleRequirements" src/
```

Expected: no output (no matches).
