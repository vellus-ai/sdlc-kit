"""Tests for sdlc-init/scripts/scaffold.py — canonical vault scaffolding.

The scaffold script walks `assets/vault-tree/` and materialises it into a
vault root, replacing `{{PLACEHOLDERS}}` in `.tpl`/`.md` files and writing
a `.sdlc-kit/marker.json`. It is idempotent by default and only overwrites
existing files when `--force` is supplied.

All tests target a throwaway path under `tmp_path` and use `--skip-git-check`
so we never depend on the plugin repo's own git state.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "sdlc-init" / "scripts" / "scaffold.py"
VAULT_TREE = REPO_ROOT / "assets" / "vault-tree"


# Canonical phases shipped with the kit. If this list changes, the scaffold
# contract has changed — bump the assertion below intentionally.
CANONICAL_PHASES = [
    "00-steering",
    "01-planning",
    "02-architecture",
    "03-domain",
    "04-specs",
    "05-development",
    "06-design-system",
    "07-retrospectives",
]


def _run_scaffold(vault_root: Path, *extra: str) -> subprocess.CompletedProcess:
    assert SCRIPT.exists(), f"missing script: {SCRIPT}"
    args = [
        sys.executable,
        str(SCRIPT),
        "--vault-root",
        str(vault_root),
        "--project-name",
        "Acme App",
        "--owner",
        "Milton <milton@example.com>",
        "--stack",
        "Go + Next.js",
        "--repo-url",
        "https://github.com/acme/app",
        "--skip-git-check",
        *extra,
    ]
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _payload(cp: subprocess.CompletedProcess) -> dict:
    assert cp.stdout.strip(), f"empty stdout; stderr={cp.stderr!r}"
    return json.loads(cp.stdout)


def _vault_target(tmp_path: Path) -> Path:
    """Return a vault path nested deep enough to pass the sensitive-path guard.

    `verify_not_system_path` refuses paths that are fewer than 2 levels below
    HOME. pytest's `tmp_path` is under the system temp dir — outside HOME on
    Windows — so any nested child works, but we nest twice for safety across
    platforms.
    """
    vault = tmp_path / "workspace" / "project" / ".sdlc"
    return vault


class TestScaffoldFreshVault:
    def test_clean_scaffold_succeeds(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, f"stderr={cp.stderr!r}\nstdout={cp.stdout!r}"
        data = _payload(cp)
        assert data["status"] == "ok"
        assert data["errors"] == []
        assert data["summary"]["created"] > 0
        assert data["summary"]["skipped"] == 0
        assert data["summary"]["updated"] == 0

    def test_all_canonical_phases_are_created(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        for phase in CANONICAL_PHASES:
            assert (vault / phase).is_dir(), f"missing phase dir: {phase}"

    def test_top_level_artifacts_are_materialised(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        # CLAUDE.md and _INDEX.md come from .tpl sources — `.tpl` suffix must
        # be stripped.
        assert (vault / "CLAUDE.md").is_file()
        assert (vault / "_INDEX.md").is_file()
        # dashboard.html is copied verbatim (non-template).
        assert (vault / "dashboard.html").is_file()

    def test_marker_has_expected_shape(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        marker = vault / ".sdlc-kit" / "marker.json"
        assert marker.is_file(), "marker.json missing"
        data = json.loads(marker.read_text(encoding="utf-8"))
        assert data["version"] == "0.1.0"
        assert data["project_name"] == "Acme App"
        assert data["owner"] == "Milton <milton@example.com>"
        assert data["stack"] == "Go + Next.js"
        assert data["repo_url"] == "https://github.com/acme/app"
        # ISO-8601 date (YYYY-MM-DD, exactly 10 chars).
        assert isinstance(data["created"], str)
        assert len(data["created"]) == 10
        assert data["created"][4] == "-" and data["created"][7] == "-"

    def test_placeholders_are_substituted_in_claude_md(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        text = (vault / "CLAUDE.md").read_text(encoding="utf-8")
        # Real project data should be present...
        assert "Acme App" in text
        # ...and placeholders should be gone.
        assert "{{PROJECT_NAME}}" not in text
        assert "{{OWNER}}" not in text
        assert "{{STACK}}" not in text
        assert "{{REPO_URL}}" not in text
        assert "{{DATE}}" not in text

    def test_templates_directories_keep_tpl_suffix(self, tmp_path):
        """Files under `_templates/` are opaque assets for consumer skills:
        they must keep their `.tpl` suffix and preserve placeholders so the
        downstream skill can render them per artifact."""
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        templates = list(vault.rglob("_templates/*"))
        assert templates, "no files under any _templates/ dir — check walk_assets"
        tpl_files = [p for p in templates if p.is_file() and p.suffix == ".tpl"]
        assert tpl_files, "expected at least one .tpl in _templates/"
        # A template file's placeholders must remain unsubstituted.
        for tpl in tpl_files:
            content = tpl.read_text(encoding="utf-8")
            if "{{" in content:
                # At least one template must retain a placeholder.
                return
        pytest.fail("no template under _templates/ kept any {{PLACEHOLDER}}")


class TestScaffoldIdempotency:
    def test_rerun_skips_all_existing_files(self, tmp_path):
        vault = _vault_target(tmp_path)
        first = _run_scaffold(vault)
        assert first.returncode == 0, first.stderr
        first_report = _payload(first)
        assert first_report["summary"]["created"] > 0

        second = _run_scaffold(vault)
        assert second.returncode == 0, second.stderr
        second_report = _payload(second)
        assert second_report["status"] == "ok"
        # Every file created on run 1 must be skipped on run 2.
        assert second_report["summary"]["created"] == 0
        assert second_report["summary"]["updated"] == 0
        assert second_report["summary"]["skipped"] == first_report["summary"]["created"]

    def test_existing_file_preserved_without_force(self, tmp_path):
        vault = _vault_target(tmp_path)
        # First scaffold so the target file exists, then manually corrupt it.
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        claude = vault / "CLAUDE.md"
        claude.write_text("HAND-EDITED CONTENT\n", encoding="utf-8")

        # Re-run without --force: the hand-edit must be preserved.
        cp2 = _run_scaffold(vault)
        assert cp2.returncode == 0, cp2.stderr
        data = _payload(cp2)
        assert "CLAUDE.md" in data["files_skipped"]
        assert claude.read_text(encoding="utf-8") == "HAND-EDITED CONTENT\n"

    def test_force_overwrites_existing_file(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault)
        assert cp.returncode == 0, cp.stderr
        claude = vault / "CLAUDE.md"
        claude.write_text("HAND-EDITED CONTENT\n", encoding="utf-8")

        cp2 = _run_scaffold(vault, "--force")
        assert cp2.returncode == 0, cp2.stderr
        data = _payload(cp2)
        # With --force, pre-existing files are reported as "updated", not skipped.
        assert "CLAUDE.md" in data["files_updated"]
        assert data["summary"]["updated"] > 0
        # And the content was regenerated from template.
        regenerated = claude.read_text(encoding="utf-8")
        assert regenerated != "HAND-EDITED CONTENT\n"
        assert "Acme App" in regenerated


class TestScaffoldDryRun:
    def test_dry_run_creates_no_files(self, tmp_path):
        vault = _vault_target(tmp_path)
        cp = _run_scaffold(vault, "--dry-run")
        assert cp.returncode == 0, cp.stderr
        data = _payload(cp)
        assert data["status"] == "dry-run"
        assert data["summary"]["created"] > 0  # reports what *would* be created
        # Nothing should actually exist on disk.
        assert not vault.exists() or not any(vault.rglob("*.md"))


class TestScaffoldSafety:
    def test_rejects_home_directory(self, tmp_path):
        # Trying to scaffold directly at HOME must fail with exit 1.
        home = str(Path.home())
        cp = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--vault-root",
                home,
                "--project-name",
                "x",
                "--skip-git-check",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert cp.returncode == 1, f"expected exit 1, got {cp.returncode}"
        data = _payload(cp)
        assert data["status"] == "error"
        assert any("sensitive" in e or "too close" in e for e in data["errors"])


class TestScaffoldDefaults:
    def test_owner_defaults_when_empty(self, tmp_path):
        """When --owner is empty the marker records an empty string, but
        the CLAUDE.md rendering must substitute the human placeholder."""
        vault = tmp_path / "workspace" / "project" / ".sdlc"
        cp = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--vault-root",
                str(vault),
                "--project-name",
                "Bare",
                "--skip-git-check",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert cp.returncode == 0, cp.stderr
        # Marker keeps the raw empty owner (source-of-truth data).
        marker = json.loads((vault / ".sdlc-kit" / "marker.json").read_text(encoding="utf-8"))
        assert marker["owner"] == ""
        assert marker["project_name"] == "Bare"
        # CLAUDE.md uses the human-friendly fallback.
        claude_text = (vault / "CLAUDE.md").read_text(encoding="utf-8")
        assert "{{OWNER}}" not in claude_text
