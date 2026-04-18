"""Tests for sdlc-review — code review records with **two axes**:
`transition` flips `status:` (draft → final) and `decide` flips
`decision:` (pending → approved | approved-with-comments |
changes-requested). Scaffold accepts --pr, --pr-url, --author for
frontmatter pre-fill.
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


class TestReviewSkill:
    SCRIPT = "sdlc-review/scripts/review.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "07-retrospectives")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["reviews"] == []

    def test_scaffold_happy_path(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-42-login", "--title", "PR 42 — Login",
            "--owner", "reviewer-a",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "pr-42-login"
        assert data["was_new"] is True
        target = vault / "07-retrospectives" / "reviews" / "pr-42-login.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "pr-42-login"
        assert fm["status"] == "draft"
        assert fm["decision"] == "pending"
        assert fm["owner"] == "reviewer-a"
        assert fm["reviewer"] == "reviewer-a"

    def test_scaffold_with_pr_metadata(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-42", "--title", "PR 42",
            "--pr", "42",
            "--pr-url", "https://github.com/acme/repo/pull/42",
            "--author", "jane-dev",
        ])
        assert cp.returncode == 0, cp.stderr
        fm = read_frontmatter(vault / "07-retrospectives" / "reviews" / "pr-42.md")
        assert fm["pr"] == "42"
        assert fm["pr_url"] == "https://github.com/acme/repo/pull/42"
        assert fm["author"] == "jane-dev"

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-01", "--title", "PR 01", "--pr", "1",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["reviews"][0]["slug"] == "pr-01"
        assert data["reviews"][0]["decision"] == "pending"
        assert data["reviews"][0]["pr"] == "1"

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
            "--slug", "pr-1", "--title", "PR 1",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1

    def test_scaffold_collision_with_force(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1 v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    # --- transition (status axis) ---
    def test_transition_draft_to_final(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "pr-1", "--to", "final",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "final"
        fm = read_frontmatter(vault / "07-retrospectives" / "reviews" / "pr-1.md")
        assert fm["status"] == "final"
        # The decision axis should NOT have been touched.
        assert fm["decision"] == "pending"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "pr-1", "--to", "draft",
        ])
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

    # --- decide (decision axis) ---
    def test_decide_to_approved(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "decide",
            "--slug", "pr-1", "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_decision"] == "pending"
        assert data["new_decision"] == "approved"
        fm = read_frontmatter(vault / "07-retrospectives" / "reviews" / "pr-1.md")
        assert fm["decision"] == "approved"
        # Status axis untouched.
        assert fm["status"] == "draft"

    def test_decide_changes_requested(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "decide",
            "--slug", "pr-1", "--to", "changes-requested",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_decision"] == "changes-requested"
        fm = read_frontmatter(vault / "07-retrospectives" / "reviews" / "pr-1.md")
        assert fm["decision"] == "changes-requested"

    def test_decide_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "decide",
            "--slug", "pr-1", "--to", "pending",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_decision"] == "pending"
        assert data["new_decision"] == "pending"

    def test_decide_invalid_value(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "pr-1", "--title", "PR 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "decide",
            "--slug", "pr-1", "--to", "bogus-value",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid decision" in e for e in data["errors"])

    def test_decide_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "decide",
            "--slug", "ghost", "--to", "approved",
        ])
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
