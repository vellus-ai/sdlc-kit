"""Integration tests for sdlc-sync (librarian)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests._skill_helpers import make_vault, parse_json, run_script

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _init_db(vault: Path) -> None:
    """Bootstrap the SQLite tracker — the sync script expects it to exist."""
    subprocess.run(
        [
            sys.executable, "-c",
            f"import sys; sys.path.insert(0, r'{PLUGIN_ROOT}'); "
            "from core.db import connect, run_migrations; "
            f"conn = connect(r'{vault}/.sdlc-kit/db.sqlite'); run_migrations(conn)",
        ],
        capture_output=True, text=True, check=False,
    )


class TestSyncHappyPath:
    def test_empty_vault_scans_zero_notes(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        _init_db(vault)
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["scanned"] >= 0

    def test_regenerates_index(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning", "02-architecture")
        _init_db(vault)
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0, cp.stderr
        assert (vault / "_INDEX.md").exists()

    def test_idempotent_second_run(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        _init_db(vault)
        run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0


class TestSyncValidation:
    def test_detects_missing_frontmatter_type(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        _init_db(vault)
        bad = vault / "01-planning" / "bad.md"
        bad.write_text("---\ntitle: Missing Type\nstatus: draft\n---\n\nBody.\n", encoding="utf-8")
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0
        data = parse_json(cp)
        assert any(a["type"] == "missing_field" for a in data.get("anomalies", []))

    def test_accepts_valid_prd(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        _init_db(vault)
        (vault / "01-planning" / "prd").mkdir(parents=True, exist_ok=True)
        prd = vault / "01-planning" / "prd" / "my-initiative.md"
        prd.write_text(
            '---\ntype: prd\ntitle: "My Initiative"\nslug: "my-initiative"\nstatus: draft\n---\n\nBody.\n',
            encoding="utf-8",
        )
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0
        data = parse_json(cp)
        missing = [a for a in data.get("anomalies", []) if a["type"] == "missing_field"]
        assert not any(a["file"].endswith("my-initiative.md") for a in missing)


class TestSyncErrors:
    def test_not_a_vault(self, tmp_path: Path) -> None:
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(tmp_path)])
        assert cp.returncode != 0


class TestSyncI18n:
    def test_index_defaults_to_ptbr(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        _init_db(vault)
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0
        idx = (vault / "_INDEX.md").read_text(encoding="utf-8")
        assert "## Panorama" in idx  # pt-BR heading

    def test_index_with_locale_en(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        # Force locale=en in marker.json
        marker = vault / ".sdlc-kit" / "marker.json"
        import json as _json
        data = _json.loads(marker.read_text(encoding="utf-8"))
        data["locale"] = "en"
        marker.write_text(_json.dumps(data), encoding="utf-8")
        _init_db(vault)
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0
        idx = (vault / "_INDEX.md").read_text(encoding="utf-8")
        assert "## Overview" in idx   # EN heading
        assert "## Panorama" not in idx  # no pt-BR leakage

    def test_moc_artifacts_empty_state_uses_locale(self, tmp_path):
        vault = make_vault(tmp_path, "02-architecture")
        _init_db(vault)
        # Force EN
        marker = vault / ".sdlc-kit" / "marker.json"
        import json as _json
        data = _json.loads(marker.read_text(encoding="utf-8"))
        data["locale"] = "en"
        marker.write_text(_json.dumps(data), encoding="utf-8")
        cp = run_script("sdlc-sync/scripts/sync.py", ["--vault-root", str(vault)])
        assert cp.returncode == 0
        # The _MOC.md for 02-architecture should exist and have EN empty-state.
        moc = (vault / "02-architecture" / "_MOC.md").read_text(encoding="utf-8")
        assert "_No artifacts yet._" in moc
