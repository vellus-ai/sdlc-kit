"""Tests for sdlc-epic — slugged epics under `01-planning/epic/`.

Lifecycle: planned (default) → in-progress → done, with cancelled
as a terminal escape hatch. Collection (many per vault), slug
required, never auto-overwritten.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)


class TestEpicSkill:
    SCRIPT = "sdlc-epic/scripts/epic.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "01-planning")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["epics"] == []

    def test_scaffold_happy_path(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "checkout-flow", "--title", "Checkout Flow",
            "--owner", "squad-payments",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "checkout-flow"
        assert data["was_new"] is True
        target = vault / "01-planning" / "epic" / "checkout-flow.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "checkout-flow"
        assert fm["status"] == "planned"
        assert fm["owner"] == "squad-payments"

    def test_scaffold_uses_marker_owner_as_fallback(self, tmp_path):
        """--owner is optional; missing value falls back to marker.json owner."""
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "ownerless", "--title", "No owner flag",
        ])
        assert cp.returncode == 0, cp.stderr
        fm = read_frontmatter(vault / "01-planning" / "epic" / "ownerless.md")
        assert fm["owner"] == "team-alpha"  # from make_vault marker default

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "discovery", "--title", "Discovery",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["epics"][0]["slug"] == "discovery"
        assert data["epics"][0]["status"] == "planned"

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "Bad_Slug", "--title", "Bad",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "dup", "--title", "Dup",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("already exists" in e for e in data["errors"])

    def test_scaffold_collision_with_force(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "dup", "--title", "Dup",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "dup", "--title", "Dup v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_transition_planned_to_in_progress(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "e1", "--title", "E1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "e1", "--to", "in-progress",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "planned"
        assert data["new_status"] == "in-progress"
        fm = read_frontmatter(vault / "01-planning" / "epic" / "e1.md")
        assert fm["status"] == "in-progress"

    def test_transition_to_done(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "e2", "--title", "E2",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "e2", "--to", "done",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "done"

    def test_transition_to_cancelled(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "e3", "--title", "E3",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "e3", "--to", "cancelled",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "cancelled"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "e4", "--title", "E4",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "e4", "--to", "planned",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "planned"
        assert data["new_status"] == "planned"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "ghost", "--to", "done",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_transition_invalid_status_rejected_by_argparse(self, tmp_path):
        """argparse enforces --to choices: planned | in-progress | done | cancelled."""
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "e5", "--title", "E5",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "e5", "--to", "shipped",
        ])
        assert cp.returncode == 2
        assert "invalid choice" in cp.stderr

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])
