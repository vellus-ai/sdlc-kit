"""Tests for sdlc-prd — slugged Product Requirements Documents under
`01-planning/prd/`.

Lifecycle: draft → active → shipped → archived. Collection (many per
vault), slug required, never auto-overwritten.
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


class TestPrdSkill:
    SCRIPT = "sdlc-prd/scripts/prd.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "01-planning")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["prds"] == []

    def test_scaffold_happy_path(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "billing-revamp", "--title", "Billing Revamp",
            "--owner", "product-lead",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "billing-revamp"
        assert data["was_new"] is True
        target = vault / "01-planning" / "prd" / "billing-revamp.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "billing-revamp"
        assert fm["status"] == "draft"
        assert fm["owner"] == "product-lead"

    def test_scaffold_uses_marker_owner_as_fallback(self, tmp_path):
        """--owner is optional; missing value falls back to marker.json owner."""
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "ownerless", "--title", "No owner flag",
        ])
        assert cp.returncode == 0, cp.stderr
        fm = read_frontmatter(vault / "01-planning" / "prd" / "ownerless.md")
        assert fm["owner"] == "team-alpha"  # from make_vault marker default

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "onboarding-v2", "--title", "Onboarding v2",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["prds"][0]["slug"] == "onboarding-v2"
        assert data["prds"][0]["status"] == "draft"

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
            "--slug", "dup-prd", "--title", "Dup",
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
            "--slug", "dup-prd", "--title", "Dup",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "dup-prd", "--title", "Dup v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_transition_draft_to_active(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "p1", "--title", "P1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "p1", "--to", "active",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "active"
        fm = read_frontmatter(vault / "01-planning" / "prd" / "p1.md")
        assert fm["status"] == "active"

    def test_transition_to_shipped(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "p2", "--title", "P2",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "p2", "--to", "shipped",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "shipped"

    def test_transition_to_archived(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "p3", "--title", "P3",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "p3", "--to", "archived",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "archived"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "p4", "--title", "P4",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "p4", "--to", "draft",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "draft"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "ghost", "--to", "active",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_transition_invalid_status_rejected_by_argparse(self, tmp_path):
        """argparse enforces --to choices: draft | active | shipped | archived."""
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "p5", "--title", "P5",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "p5", "--to", "in-progress",
        ])
        assert cp.returncode == 2
        assert "invalid choice" in cp.stderr

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])
