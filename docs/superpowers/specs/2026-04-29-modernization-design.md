# confp Modernization — 0.4.1 to 1.0.0

## Goal

Bring confp up to modern Python packaging and compatibility standards. No new features, no restructuring — just make it buildable and installable on current Python.

## Version

0.4.1 → 1.0.0 (breaking: dropped Python <3.10, removed runtime auto-install of backend deps)

## Packaging

Replace `setup.py`, `Pipfile`, `Pipfile.lock` with a single `pyproject.toml` using uv.

- Build system: hatchling (or setuptools — whichever is simpler)
- `src/` layout preserved
- Core deps: `jinja2`, `pyyaml`, `cerberus`
- Optional extras:
  - `confp[redis]` → `redis`
  - `confp[etcd]` → `python-etcd`
  - `confp[terraform]` → `boto3`
- Dev deps: `pytest`
- `uv.lock` replaces `Pipfile.lock`
- `setup.cfg` retained for bamp config, updated to point at both `setup.cfg` and `pyproject.toml` for version string

## Python compat cleanup

Minimum Python 3.10. Remove all Python 2 compatibility code:

- Remove `from __future__ import print_function` / `absolute_import` from all files
- Remove Python 2/3 `urlparse` try/except in `backends/__init__.py` — use `from urllib.parse import urlparse` directly
- Change `BackendBase(object)` + `__metaclass__ = ABCMeta` to `BackendBase(ABC)`

## Backend dependency handling

Remove `install_missing_requirements()` entirely. Users install backend deps via extras.

- Delete `install_missing_requirements()` from `backends/__init__.py`
- Remove its import and call in `__main__.py` (atomic with above)
- Remove `REQUIREMENTS` tuples from `redis.py`, `etcd.py`, `terraform_s3.py`
- Remove `CannotInstallModuleRequirements` from `exceptions.py`
- Remove `pkg_resources` import from `backends/__init__.py`
- Add `ImportError` handling in each backend's `connect()` method with a message like: `pip install confp[redis]`

## Dockerfile

- Rebase from `python:3.6-alpine3.7` to `python:3.12-alpine`
- Use `uv` instead of Pipenv for install
- Keep entrypoint: `python -m confp`

## File changes

### New
- `pyproject.toml`

### Modified
- `setup.cfg` — version → 1.0.0, bamp files includes `pyproject.toml`
- `src/confp/backends/__init__.py` — remove `install_missing_requirements()`, Py2 cruft, use `ABC`
- `src/confp/backends/redis.py` — remove `__future__` import, `REQUIREMENTS`, add `ImportError` guidance
- `src/confp/backends/etcd.py` — same
- `src/confp/backends/terraform_s3.py` — same
- `src/confp/__main__.py` — remove `__future__` import, remove `install_missing_requirements` import/call
- `src/confp/exceptions.py` — remove `CannotInstallModuleRequirements`
- `Dockerfile` — rebase, use uv

### Deleted
- `setup.py`
- `Pipfile`
- `Pipfile.lock`

## Non-goals

- No type hints
- No CI/GitHub Actions
- No new features or backends
- No code restructuring beyond removing dead compat code
- No changes to tests (existing env backend test should still pass)
