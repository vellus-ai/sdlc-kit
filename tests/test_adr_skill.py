"""Tests for sdlc-adr — Architecture Decision Records under
`02-architecture/adr/` with auto-numbered filenames `ADR-NNNN-<slug>.md`.

Lifecycle (MADR-ish): proposed -> accepted / rejected / superseded / deprecated.

Notes on behaviour discovered by reading the script:
- `new` always picks `max(existing) + 1`, so re-running with the same --slug
  produces a *new* ADR with a bumped number, not a collision error. Slugs are
  therefore not unique on disk; the numeric id is.
- `--id` for `transition` accepts `3`, `0003`, `ADR-3`, or `ADR-0003`.
- The target directory is lowercase `adr/` (script constant), even though the
  skill is conventionally referred to as "ADR".
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)


# Mirrors the filename regex the script uses (kept independent so the test
# doesn't depend on importing the SUT's module).
_ADR_FILENAME_RE = re.compile(r"^ADR-(\d{4})-([a-z0-9][a-z0-9-]*)\.md$")


class TestAdrSkill:
    SCRIPT = "sdlc-adr/scripts/adr.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "02-architecture")

    # ---------- list ----------

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0
        assert data["adrs"] == []

    def test_list_after_new(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "Adopt PostgreSQL",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 1
        entry = data["adrs"][0]
        assert entry["id"] == "ADR-0001"
        assert entry["number"] == 1
        assert entry["slug"] == "adopt-postgresql"
        assert entry["status"] == "proposed"

    # ---------- new ----------

    def test_new_first_creates_adr_0001(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "Adopt PostgreSQL", "--owner", "tech-lead",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["adr_id"] == "ADR-0001"
        assert data["number"] == 1
        assert data["slug"] == "adopt-postgresql"
        assert data["was_new"] is True
        target = vault / "02-architecture" / "adr" / "ADR-0001-adopt-postgresql.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["title"] == "Adopt PostgreSQL"
        assert fm["slug"] == "adopt-postgresql"
        assert fm["status"] == "proposed"
        assert fm["owner"] == "tech-lead"
        # `id` placeholder `ADR-NNNN` gets substituted with the resolved id.
        assert fm["id"] == "ADR-0001"
        # Heading `# ADR-NNNN — {{TITLE}}` also picks up the substitution.
        body = target.read_text(encoding="utf-8")
        assert "# ADR-0001 — Adopt PostgreSQL" in body
        assert "ADR-NNNN" not in body  # no stray unresolved placeholders

    def test_new_second_increments_to_adr_0002(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "Adopt PostgreSQL",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "Use gRPC",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["adr_id"] == "ADR-0002"
        assert data["number"] == 2
        assert (vault / "02-architecture" / "adr" / "ADR-0002-use-grpc.md").exists()

    def test_new_same_slug_twice_produces_two_distinct_numbered_files(self, tmp_path):
        """Re-running `new` with the same slug does NOT collide — the script
        always picks max(number)+1, so you get two ADRs with the same slug but
        different numbers. Slugs are not unique; numbers are.
        """
        vault = self._vault(tmp_path)
        cp1 = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--slug", "dup-slug", "--title", "First take",
        ])
        assert cp1.returncode == 0
        cp2 = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--slug", "dup-slug", "--title", "Second take",
        ])
        assert cp2.returncode == 0, cp2.stderr
        data2 = parse_json(cp2)
        assert data2["adr_id"] == "ADR-0002"
        adr_dir = vault / "02-architecture" / "adr"
        assert (adr_dir / "ADR-0001-dup-slug.md").exists()
        assert (adr_dir / "ADR-0002-dup-slug.md").exists()

    def test_new_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "whatever", "--slug", "Bad_Slug",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    def test_new_slugifies_title_when_no_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
            "--title", "Use HTTP/2 Everywhere!",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        # slugify drops non-alnum and collapses whitespace to `-`.
        assert data["slug"] == "use-http2-everywhere"

    def test_new_requires_title(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("--title" in e for e in data["errors"])

    # ---------- transition ----------

    def test_transition_proposed_to_accepted(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new", "--title", "T",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--id", "1", "--to", "accepted",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["adr_id"] == "ADR-0001"
        assert data["previous_status"] == "proposed"
        assert data["new_status"] == "accepted"

    def test_transition_through_each_lifecycle_state(self, tmp_path):
        """Each valid terminal status is reachable from `proposed`. We verify
        by scaffolding a fresh ADR per target state (the FSM is otherwise
        permissive — the script doesn't enforce directional flow)."""
        vault = self._vault(tmp_path)
        for target_status in ("accepted", "rejected", "superseded", "deprecated"):
            cp_new = run_script(self.SCRIPT, [
                "--vault-root", str(vault), "--action", "new",
                "--title", f"Decision {target_status}",
            ])
            new_data = parse_json(cp_new)
            cp = run_script(self.SCRIPT, [
                "--vault-root", str(vault), "--action", "transition",
                "--id", new_data["adr_id"], "--to", target_status,
            ])
            assert cp.returncode == 0, cp.stderr
            data = parse_json(cp)
            assert data["previous_status"] == "proposed"
            assert data["new_status"] == target_status

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new", "--title", "T",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--id", "ADR-0001", "--to", "proposed",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "proposed"
        assert data["new_status"] == "proposed"

    def test_transition_accepts_multiple_id_formats(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "new", "--title", "T",
        ])
        for raw_id in ("1", "0001", "ADR-1", "ADR-0001"):
            cp = run_script(self.SCRIPT, [
                "--vault-root", str(vault), "--action", "transition",
                "--id", raw_id, "--to", "accepted",
            ])
            assert cp.returncode == 0, f"{raw_id}: {cp.stderr}"
            data = parse_json(cp)
            assert data["adr_id"] == "ADR-0001"

    def test_transition_unknown_id(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--id", "ADR-9999", "--to", "accepted",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_transition_invalid_id_format(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--id", "not-a-number", "--to", "accepted",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid ADR id" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1

    # ---------- PBT: filename round-trip is a bijection ----------

    @pytest.mark.parametrize("number", list(range(1, 100)))
    def test_filename_format_is_bijective(self, number):
        """For every N in 1..99, formatting the ADR filename and parsing it
        back yields the original (number, slug) pair.

        This guards the invariant that the script relies on in `scan_adrs`:
        filenames must be fully recoverable from disk into a (number, slug)
        tuple with no ambiguity.
        """
        slug = f"decision-{number:02d}"
        filename = f"ADR-{number:04d}-{slug}.md"
        m = _ADR_FILENAME_RE.match(filename)
        assert m is not None, f"filename did not match canonical regex: {filename}"
        recovered_number = int(m.group(1))
        recovered_slug = m.group(2)
        assert recovered_number == number
        assert recovered_slug == slug
