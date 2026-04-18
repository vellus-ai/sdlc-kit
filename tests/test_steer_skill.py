"""Tests for sdlc-steer — three singleton steering documents
(product, tech, standards) under `00-steering/`.

Actions: status (enumerate), scaffold (materialize from template),
promote (flip draft → active).

Note: the script exposes `--action status` (not `list`) and
`--action promote` (not `transition`). Promote only supports
draft → active; there is no active → archived transition for
steering docs (they are singleton, evolving documents).
"""
from __future__ import annotations

from pathlib import Path

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)


class TestSteerSkill:
    SCRIPT = "sdlc-steer/scripts/steer.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "00-steering")

    def test_status_empty(self, tmp_path):
        """With no scaffolded docs the report lists all three as absent."""
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "status"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["action"] == "status"
        assert len(data["docs"]) == 3
        for doc in data["docs"]:
            assert doc["exists"] is False
            assert doc["name"] in ("product", "tech", "standards")
        # First missing doc is suggested next
        assert data["next_suggested"] == "product"

    def test_scaffold_product(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "product",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["doc"] == "product"
        assert data["was_new"] is True
        target = vault / "00-steering" / "product.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["status"] == "draft"
        assert fm["slug"] == "product"

    def test_scaffold_tech(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "tech",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["doc"] == "tech"
        assert data["was_new"] is True
        assert (vault / "00-steering" / "tech.md").exists()

    def test_scaffold_standards(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "standards",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["doc"] == "standards"
        assert data["was_new"] is True
        assert (vault / "00-steering" / "standards.md").exists()

    def test_status_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "product",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "status"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        product = next(d for d in data["docs"] if d["name"] == "product")
        assert product["exists"] is True
        assert product["status"] == "draft"
        # Next suggested now jumps to the first still-missing doc
        assert data["next_suggested"] == "tech"

    def test_promote_flips_draft_to_active(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "product",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "promote",
            "--doc", "product",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "active"
        fm = read_frontmatter(vault / "00-steering" / "product.md")
        assert fm["status"] == "active"

    def test_promote_idempotent_when_active(self, tmp_path):
        """Second promote on an already-active doc is a no-op."""
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "tech",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "promote",
            "--doc", "tech",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "promote",
            "--doc", "tech",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "active"
        assert data["new_status"] == "active"

    def test_scaffold_invalid_doc_rejected_by_argparse(self, tmp_path):
        """argparse enforces --doc choices: product | tech | standards."""
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "roadmap",
        ])
        assert cp.returncode == 2
        assert "invalid choice" in cp.stderr

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--doc", "product",
        ]
        first = run_script(self.SCRIPT, args)
        assert first.returncode == 0, first.stderr
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("already exists" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        """Missing `.sdlc-kit/` marker must fail with user-error exit 1."""
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "status"])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])
