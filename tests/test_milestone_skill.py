"""Tests for sdlc-milestone — delivery windows under
`01-planning/milestone/<slug>.md` with RAG-style lifecycle:
planned -> on-track -> at-risk -> slipped -> done (+ cancelled).

Scaffold optionally accepts --target-date YYYY-MM-DD to pre-fill the
`target_date:` frontmatter field.
"""
from __future__ import annotations

from pathlib import Path

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)


class TestMilestoneSkill:
    SCRIPT = "sdlc-milestone/scripts/milestone.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "01-planning")

    # ---------- list ----------

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["milestones"] == []

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
            "--owner", "pm-team",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 1
        entry = data["milestones"][0]
        assert entry["slug"] == "q2-launch"
        assert entry["status"] == "planned"
        assert entry["owner"] == "pm-team"

    # ---------- scaffold ----------

    def test_scaffold_happy_path(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
            "--owner", "delivery-lead",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "q2-launch"
        assert data["was_new"] is True
        target = vault / "01-planning" / "milestone" / "q2-launch.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "q2-launch"
        assert fm["title"] == "Q2 Launch"
        assert fm["status"] == "planned"
        assert fm["owner"] == "delivery-lead"
        # No --target-date supplied: the template's empty default is preserved.
        assert fm["target_date"] == ""

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
            "--slug", "q2-launch", "--title", "X",
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
            "--slug", "q2-launch", "--title", "X",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "X v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    # ---------- scaffold --target-date ----------

    def test_scaffold_with_target_date_injects_frontmatter(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
            "--target-date", "2026-06-30",
        ])
        assert cp.returncode == 0, cp.stderr
        target = vault / "01-planning" / "milestone" / "q2-launch.md"
        fm = read_frontmatter(target)
        # The placeholder in the template is replaced in-place (not duplicated).
        assert fm["target_date"] == "2026-06-30"
        # Raw file content should contain the dated frontmatter line exactly once.
        text = target.read_text(encoding="utf-8")
        assert text.count('target_date: "2026-06-30"') == 1

    def test_scaffold_invalid_target_date(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
            "--target-date", "30/06/2026",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid --target-date" in e for e in data["errors"])

    # ---------- transition ----------

    def test_transition_planned_to_on_track(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "q2-launch", "--to", "on-track",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "planned"
        assert data["new_status"] == "on-track"
        fm = read_frontmatter(vault / "01-planning" / "milestone" / "q2-launch.md")
        assert fm["status"] == "on-track"

    def test_transition_through_full_lifecycle(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
        ])
        path = vault / "01-planning" / "milestone" / "q2-launch.md"
        for target_status in ("on-track", "at-risk", "slipped", "done"):
            cp = run_script(self.SCRIPT, [
                "--vault-root", str(vault), "--action", "transition",
                "--slug", "q2-launch", "--to", target_status,
            ])
            assert cp.returncode == 0, cp.stderr
            assert read_frontmatter(path)["status"] == target_status

    def test_transition_cancelled_reachable_from_planned(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "dead-letter", "--title", "Dead Letter",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "dead-letter", "--to", "cancelled",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "cancelled"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "q2-launch", "--title", "Q2 Launch",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "q2-launch", "--to", "planned",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "planned"
        assert data["new_status"] == "planned"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "ghost", "--to", "on-track",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
