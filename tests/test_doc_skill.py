"""Tests for sdlc-doc — generic scaffolder that materialises any template
from ``assets/vault-tree/<phase>/_templates/`` into the vault.

The script has four interesting paths:
- happy path: template exists, destination is free → file written, exit 0
- template missing: requested template not in ``_templates/`` → exit 1
- file collision: destination already exists (no ``--force`` flag is
  accepted by this script) → exit 1
- dry-run: nothing is written, the planned destination is reported

An additional "unknown phase" path is also covered because the script
branches on a small lookup table of phase numbers.
"""
from __future__ import annotations

from pathlib import Path

from tests._skill_helpers import make_vault, parse_json, run_script


SCRIPT = "sdlc-doc/scripts/doc.py"


class TestDocSkill:
    # ------------------------------------------------------------------
    # Happy path — render prd.md.tpl into 01-planning/
    # ------------------------------------------------------------------
    def test_happy_path_renders_template(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "User Onboarding",
            "--template", "prd.md.tpl",
            "--phase", "01",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        dest = vault / "01-planning" / "user-onboarding.md"
        assert Path(data["file"]) == dest
        assert dest.exists()
        content = dest.read_text(encoding="utf-8")
        # Template placeholders were substituted.
        assert "{{TITLE}}" not in content
        assert "User Onboarding" in content
        # {{DATE}} is replaced with an ISO date → there should be no
        # leftover placeholder. The DATE line is frontmatter `created:`.
        assert "{{DATE}}" not in content

    def test_happy_path_slugifies_title(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Billing & Invoicing — v2!",
            "--template", "prd.md.tpl",
            "--phase", "01",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        dest = Path(data["file"])
        # & and ! are stripped, em-dash is non-word so also stripped,
        # runs of whitespace collapse to a single hyphen.
        assert dest.name == "billing-invoicing-v2.md"
        assert dest.exists()

    # ------------------------------------------------------------------
    # Template missing — the filename is not in _templates/
    # ------------------------------------------------------------------
    def test_template_missing_exits_1(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Ghost",
            "--template", "does-not-exist.md.tpl",
            "--phase", "01",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "template not found" in data["message"]

    # ------------------------------------------------------------------
    # Unknown phase — phase number not in the lookup table
    # ------------------------------------------------------------------
    def test_unknown_phase_exits_1(self, tmp_path):
        vault = make_vault(tmp_path)
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Whatever",
            "--template", "prd.md.tpl",
            "--phase", "99",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "unknown phase" in data["message"]

    # ------------------------------------------------------------------
    # File collision — destination already exists → exit 1
    # (the script does not expose a --force flag)
    # ------------------------------------------------------------------
    def test_collision_exits_1(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        args = [
            "--vault-root", str(vault),
            "--title", "Collision Case",
            "--template", "prd.md.tpl",
            "--phase", "01",
        ]
        first = run_script(SCRIPT, args)
        assert first.returncode == 0, first.stderr

        second = run_script(SCRIPT, args)
        assert second.returncode == 1
        data = parse_json(second)
        assert data["status"] == "error"
        assert "already exists" in data["message"]

    # ------------------------------------------------------------------
    # --dry-run — no file is written, destination is reported
    # ------------------------------------------------------------------
    def test_dry_run_does_not_write(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Dry Test",
            "--template", "prd.md.tpl",
            "--phase", "01",
            "--dry-run",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "dry-run"
        planned = Path(data["destination"])
        assert planned.name == "dry-test.md"
        assert data["exists"] is False
        # Nothing was actually materialised.
        assert not planned.exists()

    def test_dry_run_reports_existing_destination(self, tmp_path):
        vault = make_vault(tmp_path, "01-planning")
        # Pre-seed the destination file by running once for real.
        run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Prior Doc",
            "--template", "prd.md.tpl",
            "--phase", "01",
        ])
        cp = run_script(SCRIPT, [
            "--vault-root", str(vault),
            "--title", "Prior Doc",
            "--template", "prd.md.tpl",
            "--phase", "01",
            "--dry-run",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "dry-run"
        assert data["exists"] is True

    # ------------------------------------------------------------------
    # Vault missing — marker absent → exit 2
    # ------------------------------------------------------------------
    def test_exits_2_when_vault_root_has_no_marker(self, tmp_path):
        not_a_vault = tmp_path / "elsewhere"
        not_a_vault.mkdir()
        cp = run_script(SCRIPT, [
            "--vault-root", str(not_a_vault),
            "--title", "X",
            "--template", "prd.md.tpl",
            "--phase", "01",
        ])
        assert cp.returncode == 2
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "not a valid vault" in data["message"]
