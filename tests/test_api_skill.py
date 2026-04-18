"""Tests for sdlc-api — 4 kinds (rest/async/grpc/webhook), all collections,
lifecycle draft → approved → deprecated. Templates live under
02-architecture/_templates/api/*.md.tpl.
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


class TestApiSkill:
    SCRIPT = "sdlc-api/scripts/api.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "02-architecture")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["artifacts"] == []

    @pytest.mark.parametrize("kind,folder", [
        ("rest", "rest"),
        ("async", "async"),
        ("grpc", "grpc"),
        ("webhook", "webhook"),
    ])
    def test_scaffold_each_kind(self, tmp_path, kind, folder):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", kind, "--slug", "payments-v1", "--title", "Payments v1",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["kind"] == kind
        assert data["slug"] == "payments-v1"
        target = vault / "02-architecture" / "api" / folder / "payments-v1.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "payments-v1"
        assert fm["status"] == "draft"

    def test_scaffold_requires_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--title", "No Slug",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("requires --slug" in e for e in data["errors"])

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "Bad_Slug", "--title", "X",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "payments-v1", "--title", "X",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1

    def test_scaffold_collision_with_force(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "payments-v1", "--title", "X",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "payments-v1", "--title", "X v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_list_kind_filter(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "rest-a", "--title", "Rest A",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "grpc", "--slug", "grpc-a", "--title", "Grpc A",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "list", "--kind", "grpc",
        ])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["artifacts"][0]["kind"] == "grpc"
        assert data["artifacts"][0]["slug"] == "grpc-a"

    def test_list_all_kinds(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "a", "--title", "A",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "webhook", "--slug", "b", "--title", "B",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        data = parse_json(cp)
        assert data["count"] == 2

    def test_transition_to_approved(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "payments-v1", "--title", "P",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "rest", "--slug", "payments-v1", "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "approved"
        fm = read_frontmatter(
            vault / "02-architecture" / "api" / "rest" / "payments-v1.md"
        )
        assert fm["status"] == "approved"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "rest", "--slug", "a", "--title", "A",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "rest", "--slug", "a", "--to", "draft",
        ])
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "draft"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "rest", "--slug", "ghost", "--to", "approved",
        ])
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
