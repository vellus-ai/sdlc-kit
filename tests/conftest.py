"""
Shared fixtures for SDLC Kit test suite.
Contains common test utilities and vault setups.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from core.db import connect, run_migrations

# Point any subprocess using our sitecustomize shim (tests/sitecustomize.py)
# at the pyproject.toml coverage config. pytest-cov sets this automatically
# for its own worker processes, but we also inherit it here for the skill
# scripts invoked via `_skill_helpers.run_script` so their line coverage is
# captured. Safe to set unconditionally — when pytest-cov is not loaded the
# sitecustomize shim is a no-op.
_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
if _PYPROJECT.exists() and "COVERAGE_PROCESS_START" not in os.environ:
    os.environ["COVERAGE_PROCESS_START"] = str(_PYPROJECT)


@pytest.fixture
def vault_dir(tmp_path):
    """Creates a minimal valid vault with marker.json."""
    kit = tmp_path / ".sdlc-kit"
    kit.mkdir()
    (kit / "marker.json").write_text(json.dumps({"version": "0.1.0"}))
    return tmp_path


@pytest.fixture
def vault_with_db(tmp_path):
    """Creates a vault with initialized SQLite database."""
    kit_dir = tmp_path / ".sdlc-kit"
    kit_dir.mkdir()
    (kit_dir / "marker.json").write_text(json.dumps({"version": "0.1.0"}))
    db_path = kit_dir / "db.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    yield tmp_path, conn
    conn.close()


@pytest.fixture
def markdown_file(tmp_path):
    """Factory fixture to create temporary markdown files."""
    def _write_md(relative_path: str, content: str) -> Path:
        """Write markdown content to a file in the vault."""
        p = tmp_path / relative_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p
    return _write_md
