"""SDLC Kit test package.

This file turns `tests/` into a proper Python package so `from tests._skill_helpers
import ...` works when the project is installed via `pip install -e .` (where
only `core`, `hooks`, `skills` are listed as packages in pyproject.toml).

Local dev picks the `tests/` directory up through pytest's rootdir discovery,
but CI runners invoke pytest from a clean venv where only the installed
packages are importable — without this `__init__.py` the helper imports fail
with `ModuleNotFoundError: No module named 'tests'`.
"""
