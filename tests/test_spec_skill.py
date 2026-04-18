"""Tests for sdlc-spec — SDD trio scaffolding/lifecycle under
`04-specs/<feature-slug>/`.

Trio: requirements.md + design.md + tasks.md, each with its own status
lifecycle (draft → approved → implemented → archived). Scaffold creates the
three files in one shot; transition flips status per-doc or for all three.
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


class TestSpecSkill:
    SCRIPT = "sdlc-spec/scripts/spec.py"

    # ------------------------------------------------------------------
    # fixtures
    # ------------------------------------------------------------------

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "04-specs")

    def _spec_dir(self, vault: Path, slug: str) -> Path:
        return vault / "04-specs" / slug

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "list",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["features"] == []

    def test_list_shows_trio_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "user-login",
            "--title", "User Login",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "list",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 1
        feature = data["features"][0]
        assert feature["slug"] == "user-login"
        kinds = sorted(d["kind"] for d in feature["docs"])
        assert kinds == ["design", "requirements", "tasks"]
        assert all(d["exists"] is True for d in feature["docs"])
        assert all(d["status"] == "draft" for d in feature["docs"])

    # ------------------------------------------------------------------
    # scaffold
    # ------------------------------------------------------------------

    def test_scaffold_creates_all_three_docs(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "api-rate-limiting",
            "--title", "API Rate Limiting",
            "--owner", "platform-lead",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "api-rate-limiting"
        assert len(data["docs"]) == 3
        assert all(d["was_new"] is True for d in data["docs"])
        assert all(d["skipped"] is False for d in data["docs"])

        spec_dir = self._spec_dir(vault, "api-rate-limiting")
        for kind in ("requirements", "design", "tasks"):
            target = spec_dir / f"{kind}.md"
            assert target.exists(), f"missing {target}"
            fm = read_frontmatter(target)
            assert fm["slug"] == "api-rate-limiting"
            assert fm["status"] == "draft"
            assert fm["owner"] == "platform-lead"
            assert fm["feature"] == "api-rate-limiting"

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "Bad_Slug",
            "--title", "Bad",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    def test_scaffold_collision_without_force_skips(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "collision",
            "--title", "Collision",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        # Every doc should be reported as skipped on the second run.
        assert all(d["skipped"] is True for d in data["docs"])
        assert all(d["was_new"] is False for d in data["docs"])

    def test_scaffold_collision_with_force_overwrites(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "forced",
            "--title", "v1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "forced",
            "--title", "v2",
            "--force",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert all(d["skipped"] is False for d in data["docs"])
        # v2 placeholders should have been applied — at least in the
        # human-readable `title:` field of the frontmatter.
        fm = read_frontmatter(
            self._spec_dir(vault, "forced") / "requirements.md"
        )
        assert "v2" in fm["title"]

    def test_scaffold_dry_run_writes_nothing(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "ghost",
            "--title", "Ghost",
            "--dry-run",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "dry-run"
        spec_dir = self._spec_dir(vault, "ghost")
        assert not spec_dir.exists(), "dry-run must not create folders"

    # ------------------------------------------------------------------
    # transition
    # ------------------------------------------------------------------

    def test_transition_requirements_to_approved(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "feature-x",
            "--title", "Feature X",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "transition",
            "--slug", "feature-x",
            "--doc", "requirements",
            "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert len(data["docs"]) == 1
        assert data["docs"][0]["kind"] == "requirements"
        assert data["docs"][0]["previous_status"] == "draft"
        assert data["docs"][0]["new_status"] == "approved"
        assert data["docs"][0]["changed"] is True

        spec_dir = self._spec_dir(vault, "feature-x")
        assert read_frontmatter(spec_dir / "requirements.md")["status"] == "approved"
        # Other two docs unaffected.
        assert read_frontmatter(spec_dir / "design.md")["status"] == "draft"
        assert read_frontmatter(spec_dir / "tasks.md")["status"] == "draft"

    def test_transition_all_docs_at_once(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "feature-all",
            "--title", "Feature All",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "transition",
            "--slug", "feature-all",
            "--doc", "all",
            "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert len(data["docs"]) == 3
        assert all(d["new_status"] == "approved" for d in data["docs"])
        assert all(d["changed"] is True for d in data["docs"])

        spec_dir = self._spec_dir(vault, "feature-all")
        for kind in ("requirements", "design", "tasks"):
            assert read_frontmatter(spec_dir / f"{kind}.md")["status"] == "approved"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "idem",
            "--title", "Idem",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "transition",
            "--slug", "idem",
            "--doc", "design",
            "--to", "draft",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["docs"][0]["previous_status"] == "draft"
        assert data["docs"][0]["new_status"] == "draft"
        assert data["docs"][0]["changed"] is False

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "transition",
            "--slug", "ghost",
            "--doc", "requirements",
            "--to", "approved",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("spec folder not found" in e for e in data["errors"])

    def test_transition_dry_run_does_not_write(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "scaffold",
            "--slug", "dry",
            "--title", "Dry",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "transition",
            "--slug", "dry",
            "--doc", "requirements",
            "--to", "approved",
            "--dry-run",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "dry-run"
        assert data["docs"][0]["changed"] is True  # would-change projection
        # But the file on disk is still draft.
        req = self._spec_dir(vault, "dry") / "requirements.md"
        assert read_frontmatter(req)["status"] == "draft"

    # ------------------------------------------------------------------
    # shared guardrails
    # ------------------------------------------------------------------

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(tmp_path),
            "--action", "list",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])
