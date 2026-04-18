"""Tests for phase-5 skills: sdlc-retro, sdlc-worktree.

Both skills expose the canonical `--action list|scaffold|transition` contract.
Retro is single-kind and supports a `--sprint` scaffold side-effect that
pre-fills the `sprint:` frontmatter field. Worktree is multi-kind
(worktree + branch) but transition is only supported for `worktree`.
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


# ---------------------------------------------------------------------------
# sdlc-retro
# ---------------------------------------------------------------------------

class TestRetroSkill:
    SCRIPT = "sdlc-retro/scripts/retro.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "07-retrospectives")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["retros"] == []

    def test_scaffold_happy_path(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-01", "--title", "Sprint 01",
            "--owner", "facilitator",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "sprint-01"
        assert data["was_new"] is True
        target = vault / "07-retrospectives" / "retros" / "sprint-01.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "sprint-01"
        assert fm["status"] == "draft"
        assert fm["owner"] == "facilitator"

    def test_scaffold_with_sprint_prefills_field(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-42", "--title", "Sprint 42",
            "--sprint", "42",
        ])
        assert cp.returncode == 0, cp.stderr
        fm = read_frontmatter(vault / "07-retrospectives" / "retros" / "sprint-42.md")
        assert fm["sprint"] == "42"

    def test_list_returns_entries(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-01", "--title", "Sprint 01",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-02", "--title", "Sprint 02", "--sprint", "2",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        data = parse_json(cp)
        assert data["count"] == 2
        slugs = sorted(r["slug"] for r in data["retros"])
        assert slugs == ["sprint-01", "sprint-02"]
        by_slug = {r["slug"]: r for r in data["retros"]}
        assert by_slug["sprint-02"]["sprint"] == "2"

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
            "--slug", "sprint-01", "--title", "Sprint 01",
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
            "--slug", "sprint-01", "--title", "Sprint 01",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-01", "--title", "Sprint 01 v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_transition_draft_to_final(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-01", "--title", "Sprint 01",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "sprint-01", "--to", "final",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "final"
        fm = read_frontmatter(vault / "07-retrospectives" / "retros" / "sprint-01.md")
        assert fm["status"] == "final"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "sprint-01", "--title", "Sprint 01",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "sprint-01", "--to", "draft",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "draft"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "ghost", "--to", "final",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1


# ---------------------------------------------------------------------------
# sdlc-worktree
# ---------------------------------------------------------------------------

class TestWorktreeSkill:
    SCRIPT = "sdlc-worktree/scripts/worktree.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "05-development")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0

    def test_scaffold_worktree(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "feat-login",
            "--title", "Login feature",
        ])
        assert cp.returncode == 0, cp.stderr
        target = vault / "05-development" / "worktrees" / "feat-login.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "feat-login"
        # worktree template default status is `active`
        assert fm["status"] == "active"

    def test_scaffold_branch(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "branch", "--slug", "feat-login",
            "--title", "Login branch",
        ])
        assert cp.returncode == 0, cp.stderr
        assert (vault / "05-development" / "branches" / "feat-login.md").exists()

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "Bad_Slug", "--title", "X",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    def test_list_kind_filter(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "feat-wt", "--title", "WT",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "branch", "--slug", "feat-br", "--title", "BR",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "list", "--kind", "worktree",
        ])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["artifacts"][0]["slug"] == "feat-wt"

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "dup", "--title", "Dup",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1

    def test_scaffold_collision_with_force(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "dup", "--title", "Dup",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "dup", "--title", "Dup v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_transition_worktree_to_merged(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "feat-x", "--title", "X",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "worktree", "--slug", "feat-x", "--to", "merged",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "active"
        assert data["new_status"] == "merged"
        fm = read_frontmatter(vault / "05-development" / "worktrees" / "feat-x.md")
        assert fm["status"] == "merged"

    def test_transition_worktree_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "worktree", "--slug", "feat-x", "--title", "X",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "worktree", "--slug", "feat-x", "--to", "active",
        ])
        data = parse_json(cp)
        assert data["previous_status"] == "active"
        assert data["new_status"] == "active"

    def test_transition_branch_is_rejected(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "branch", "--slug", "feat-br", "--title", "BR",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "branch", "--slug", "feat-br", "--to", "merged",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("no formal status" in e or "not supported" in e
                   for e in data["errors"])

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "worktree", "--slug", "ghost", "--to", "merged",
        ])
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
