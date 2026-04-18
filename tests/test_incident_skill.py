"""Tests for sdlc-incident — 4-state open → mitigated → resolved → post-mortem
with timestamp auto-fill on entering `mitigated` and `resolved`.

Scaffold accepts --severity SEV1|SEV2|SEV3|SEV4 and --detected-at YYYY-MM-DD
and pre-fills those fields in frontmatter.
"""
from __future__ import annotations

from pathlib import Path

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)


class TestIncidentSkill:
    SCRIPT = "sdlc-incident/scripts/incident.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "07-retrospectives")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["incidents"] == []

    def test_scaffold_default_severity(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-2026-04-18-api-down", "--title", "API down",
            "--detected-at", "2026-04-18",
        ])
        assert cp.returncode == 0, cp.stderr
        target = vault / "07-retrospectives" / "incidents" / "inc-2026-04-18-api-down.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "inc-2026-04-18-api-down"
        assert fm["status"] == "open"
        # default severity is SEV3 per argparse
        assert fm["severity"] == "SEV3"
        assert fm["detected_at"] == "2026-04-18"

    def test_scaffold_severity_sev1(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Big one",
            "--severity", "SEV1", "--detected-at", "2026-04-10",
        ])
        assert cp.returncode == 0, cp.stderr
        fm = read_frontmatter(vault / "07-retrospectives" / "incidents" / "inc-1.md")
        assert fm["severity"] == "SEV1"
        assert fm["detected_at"] == "2026-04-10"

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1", "--severity", "SEV2",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        data = parse_json(cp)
        assert data["count"] == 1
        row = data["incidents"][0]
        assert row["slug"] == "inc-1"
        assert row["severity"] == "SEV2"
        assert row["status"] == "open"

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
            "--slug", "inc-1", "--title", "Inc 1",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1

    def test_scaffold_collision_with_force(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1 v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    # --- transitions with timestamp auto-fill ---
    def test_transition_to_mitigated_fills_timestamp(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "mitigated",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "open"
        assert data["new_status"] == "mitigated"
        assert "mitigated_at" in data["timestamps_updated"]
        fm = read_frontmatter(vault / "07-retrospectives" / "incidents" / "inc-1.md")
        assert fm["status"] == "mitigated"
        assert fm["mitigated_at"]  # non-empty

    def test_transition_to_resolved_fills_timestamp(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        # walk open → mitigated → resolved
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "mitigated",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "resolved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert "resolved_at" in data["timestamps_updated"]
        fm = read_frontmatter(vault / "07-retrospectives" / "incidents" / "inc-1.md")
        assert fm["status"] == "resolved"
        assert fm["mitigated_at"]
        assert fm["resolved_at"]

    def test_transition_to_post_mortem_no_timestamp_sideeffect(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        # Directly flip to post-mortem (no auto-fill expected).
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "post-mortem",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "post-mortem"
        assert data["timestamps_updated"] == []

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "open",
        ])
        data = parse_json(cp)
        assert data["previous_status"] == "open"
        assert data["new_status"] == "open"
        assert data["timestamps_updated"] == []

    def test_transition_preserves_existing_timestamp(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--slug", "inc-1", "--title", "Inc 1",
        ])
        # First transition records mitigated_at.
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "mitigated",
        ])
        fm_before = read_frontmatter(
            vault / "07-retrospectives" / "incidents" / "inc-1.md"
        )
        original = fm_before["mitigated_at"]
        # Rewind to open and then re-enter mitigated. The script should NOT
        # overwrite the already-populated mitigated_at value.
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "open",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "inc-1", "--to", "mitigated",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        # Second entry sees the field non-empty → not reported as updated.
        assert data["timestamps_updated"] == []
        fm_after = read_frontmatter(
            vault / "07-retrospectives" / "incidents" / "inc-1.md"
        )
        assert fm_after["mitigated_at"] == original

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--slug", "ghost", "--to", "mitigated",
        ])
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1
