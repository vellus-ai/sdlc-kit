"""Tests for phase-4 skills: sdlc-domain, sdlc-c4, sdlc-design-system,
sdlc-trace, sdlc-impact.

All tests exercise the canonical `--action list|scaffold|transition`
contract (`analyze` for impact, `report` for trace). Skill scripts are
invoked as subprocesses so their stdin/stdout contract and exit codes are
validated end-to-end.
"""
from __future__ import annotations

from pathlib import Path

from tests._skill_helpers import (
    make_vault,
    parse_json,
    read_frontmatter,
    run_script,
)

# ---------------------------------------------------------------------------
# sdlc-domain
# ---------------------------------------------------------------------------

class TestDomainSkill:
    SCRIPT = "sdlc-domain/scripts/domain.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "03-domain")

    # --- list ---
    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["action"] == "list"
        assert data["count"] == 0
        assert data["artifacts"] == []

    def test_list_filters_by_kind(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "event", "--slug", "order-created", "--title", "OrderCreated",
        ])

        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "list", "--kind", "aggregate",
        ])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["artifacts"][0]["kind"] == "aggregate"
        assert data["artifacts"][0]["slug"] == "order"

    # --- scaffold ---
    def test_scaffold_collection_creates_file(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order", "--owner", "tech-lead",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["kind"] == "aggregate"
        assert data["slug"] == "order"
        assert data["was_new"] is True

        target = vault / "03-domain" / "aggregates" / "order.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "order"
        assert fm["status"] == "draft"
        assert fm["owner"] == "tech-lead"

    def test_scaffold_singleton_context_map(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "context-map",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "context-map"
        assert data["artifact_path"].endswith("context-map.md")
        assert (vault / "03-domain" / "context-map.md").exists()

    def test_scaffold_singleton_rejects_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "context-map", "--slug", "should-fail",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert data["status"] == "error"
        assert any("singleton" in e for e in data["errors"])

    def test_scaffold_collection_requires_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--title", "Missing Slug",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("requires --slug" in e for e in data["errors"])

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order",
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
            "--kind", "aggregate", "--slug", "order", "--title", "Order",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order v2", "--force",
        ])
        assert cp.returncode == 0, cp.stderr

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "Bad_Slug", "--title", "X",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid slug" in e for e in data["errors"])

    # --- transition ---
    def test_transition_flips_status(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "aggregate", "--slug", "order", "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "approved"

        fm = read_frontmatter(vault / "03-domain" / "aggregates" / "order.md")
        assert fm["status"] == "approved"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "aggregate", "--slug", "order", "--title", "Order",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "aggregate", "--slug", "order", "--to", "draft",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "draft"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "aggregate", "--slug", "ghost", "--to", "approved",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(tmp_path), "--action", "list",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])


# ---------------------------------------------------------------------------
# sdlc-c4
# ---------------------------------------------------------------------------

class TestC4Skill:
    SCRIPT = "sdlc-c4/scripts/c4.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "02-architecture")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0

    def test_scaffold_context_singleton(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "context",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["slug"] == "context"
        target = vault / "02-architecture" / "c4" / "context.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["status"] == "draft"

    def test_scaffold_component_requires_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "component",
            "--title", "No Slug",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("requires --slug" in e for e in data["errors"])

    def test_scaffold_component_creates_file(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "component",
            "--slug", "auth-service", "--title", "Auth Service",
        ])
        assert cp.returncode == 0, cp.stderr
        target = vault / "02-architecture" / "c4" / "components" / "auth-service.md"
        assert target.exists()

    def test_scaffold_singleton_rejects_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "context", "--slug", "ignored",
        ])
        assert cp.returncode == 1

    def test_list_after_scaffold(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "context",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "component",
            "--slug", "billing", "--title", "Billing",
        ])
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        data = parse_json(cp)
        # context singleton + billing component
        assert data["count"] == 2
        kinds = {d["kind"] for d in data["diagrams"]}
        assert kinds == {"context", "component"}

    def test_list_kind_filter(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "context",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "component",
            "--slug", "billing", "--title", "Billing",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "list", "--kind", "component",
        ])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["diagrams"][0]["slug"] == "billing"

    def test_transition_component(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold", "--kind", "component",
            "--slug", "billing", "--title", "Billing",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "component", "--slug", "billing", "--to", "approved",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "approved"
        fm = read_frontmatter(vault / "02-architecture" / "c4" / "components" / "billing.md")
        assert fm["status"] == "approved"

    def test_transition_unknown_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "component", "--slug", "ghost", "--to", "approved",
        ])
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1


# ---------------------------------------------------------------------------
# sdlc-design-system
# ---------------------------------------------------------------------------

class TestDesignSystemSkill:
    SCRIPT = "sdlc-design-system/scripts/design_system.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "06-design-system")

    def test_list_empty(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, ["--vault-root", str(vault), "--action", "list"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["count"] == 0

    def test_scaffold_token(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "color-primary-500", "--title", "Primary 500",
        ])
        assert cp.returncode == 0, cp.stderr
        target = vault / "06-design-system" / "tokens" / "color-primary-500.md"
        assert target.exists()
        fm = read_frontmatter(target)
        assert fm["slug"] == "color-primary-500"
        assert fm["status"] == "draft"

    def test_scaffold_component(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "component", "--slug", "button", "--title", "Button",
        ])
        assert cp.returncode == 0
        assert (vault / "06-design-system" / "components" / "button.md").exists()

    def test_scaffold_pattern(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "pattern", "--slug", "empty-state", "--title", "Empty State",
        ])
        assert cp.returncode == 0
        assert (vault / "06-design-system" / "patterns" / "empty-state.md").exists()

    def test_scaffold_invalid_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "Bad_Slug", "--title", "Bad",
        ])
        assert cp.returncode == 1

    def test_list_kind_filter(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "spacing-4", "--title", "Spacing 4",
        ])
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "component", "--slug", "card", "--title", "Card",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "list", "--kind", "component",
        ])
        data = parse_json(cp)
        assert data["count"] == 1
        assert data["entries"][0]["slug"] == "card"

    def test_transition_draft_to_stable(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "spacing-4", "--title", "Spacing 4",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "token", "--slug", "spacing-4", "--to", "stable",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_status"] == "stable"
        fm = read_frontmatter(vault / "06-design-system" / "tokens" / "spacing-4.md")
        assert fm["status"] == "stable"

    def test_transition_idempotent(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "spacing-4", "--title", "Spacing 4",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "transition",
            "--kind", "token", "--slug", "spacing-4", "--to", "draft",
        ])
        data = parse_json(cp)
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "draft"

    def test_scaffold_collision_without_force(self, tmp_path):
        vault = self._vault(tmp_path)
        args = [
            "--vault-root", str(vault), "--action", "scaffold",
            "--kind", "token", "--slug", "x", "--title", "X",
        ]
        run_script(self.SCRIPT, args)
        cp = run_script(self.SCRIPT, args)
        assert cp.returncode == 1

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "list"])
        assert cp.returncode == 1


# ---------------------------------------------------------------------------
# sdlc-trace (single read-only `report` action)
# ---------------------------------------------------------------------------

def _write_note(vault: Path, rel: str, frontmatter: dict, body: str = "") -> Path:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f'{k}: "{v}"' if isinstance(v, str) else f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestTraceSkill:
    SCRIPT = "sdlc-trace/scripts/trace.py"

    def _vault(self, tmp_path: Path) -> Path:
        # trace only requires the marker — it walks whatever phase folders
        # exist. We still seed a couple to make the walk meaningful.
        vault = make_vault(tmp_path, "01-planning", "04-specs", "02-architecture",
                           "07-retrospectives")
        return vault

    def test_empty_report_json(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "report",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["action"] == "report"
        assert data["format"] == "json"
        assert data["features"] == []
        assert data["orphan_adrs"] == []
        assert data["orphan_trds"] == []

    def test_full_chain_is_complete(self, tmp_path):
        vault = self._vault(tmp_path)
        _write_note(vault, "01-planning/prds/feat-a.md",
                    {"type": "prd", "slug": "feat-a", "title": "Feat A"},
                    "Links: [[feat-a-requirements]]")
        _write_note(vault, "04-specs/feat-a/feat-a-requirements.md",
                    {"type": "spec-requirements", "slug": "feat-a", "title": "Req"},
                    "See [[feat-a]]")
        _write_note(vault, "04-specs/feat-a/feat-a-design.md",
                    {"type": "spec-design", "slug": "feat-a", "title": "Des"},
                    "Based on [[feat-a]]")
        _write_note(vault, "04-specs/feat-a/feat-a-tasks.md",
                    {"type": "spec-tasks", "slug": "feat-a", "title": "Tasks"},
                    "- [ ] do thing\n- [x] done\n")

        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "report",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert len(data["features"]) == 1
        row = data["features"][0]
        assert row["slug"] == "feat-a"
        assert row["coverage_status"] == "complete"
        assert row["requirements"]["exists"] is True
        assert row["design"]["exists"] is True
        assert row["tasks"]["exists"] is True
        assert row["tasks"]["task_count"] == 2
        assert row["prd_refs"] == ["feat-a"]

    def test_partial_coverage_and_markdown(self, tmp_path):
        vault = self._vault(tmp_path)
        # only requirements — no design, no tasks, no PRD
        _write_note(vault, "04-specs/solo/solo-requirements.md",
                    {"type": "spec-requirements", "slug": "solo", "title": "Solo"}, "")
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "report", "--format", "markdown",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["format"] == "markdown"
        assert "markdown" in data
        assert "Traceability report" in data["markdown"]
        # In markdown format, features are not carried through (see docstring).
        assert "features" not in data

    def test_orphan_adr(self, tmp_path):
        vault = self._vault(tmp_path)
        _write_note(vault, "02-architecture/adr/adr-0001-x.md",
                    {"type": "adr", "slug": "adr-0001", "title": "ADR"}, "")
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "report",
        ])
        data = parse_json(cp)
        assert "adr-0001-x" in data["orphan_adrs"]

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, ["--vault-root", str(tmp_path), "--action", "report"])
        assert cp.returncode == 1


# ---------------------------------------------------------------------------
# sdlc-impact (single `analyze` action)
# ---------------------------------------------------------------------------

class TestImpactSkill:
    SCRIPT = "sdlc-impact/scripts/impact.py"

    def _vault(self, tmp_path: Path) -> Path:
        return make_vault(tmp_path, "02-architecture", "04-specs")

    def _seed_chain(self, vault: Path) -> None:
        """A → B → C, and D → A (so A has 1 forward, 1 backward dep)."""
        _write_note(vault, "02-architecture/adr/a.md",
                    {"type": "adr", "slug": "a", "title": "A"}, "Refers to [[b]]")
        _write_note(vault, "02-architecture/adr/b.md",
                    {"type": "adr", "slug": "b", "title": "B"}, "Refers to [[c]]")
        _write_note(vault, "02-architecture/adr/c.md",
                    {"type": "adr", "slug": "c", "title": "C"}, "")
        _write_note(vault, "04-specs/d/d-design.md",
                    {"type": "spec-design", "slug": "d", "title": "D"}, "Based on [[a]]")

    def test_seed_not_found(self, tmp_path):
        vault = self._vault(tmp_path)
        self._seed_chain(vault)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "does-not-exist",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not found" in e for e in data["errors"])

    def test_backward_default(self, tmp_path):
        vault = self._vault(tmp_path)
        self._seed_chain(vault)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "a",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["seed"] == "a"
        assert data["direction"] == "backward"
        stems = [n["stem"] for n in data["nodes"]]
        # backward from A: D depends on A
        assert "d-design" in stems
        assert "b" not in stems

    def test_forward_walks_outgoing(self, tmp_path):
        vault = self._vault(tmp_path)
        self._seed_chain(vault)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "a",
            "--direction", "forward", "--depth", "5",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        stems = [n["stem"] for n in data["nodes"]]
        assert "b" in stems
        assert "c" in stems

    def test_both_direction_union(self, tmp_path):
        vault = self._vault(tmp_path)
        self._seed_chain(vault)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "a",
            "--direction", "both", "--depth", "5", "--format", "markdown",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert "markdown" in data
        stems = [n["stem"] for n in data["nodes"]]
        assert "b" in stems and "d-design" in stems

    def test_depth_limits_walk(self, tmp_path):
        vault = self._vault(tmp_path)
        self._seed_chain(vault)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "a",
            "--direction", "forward", "--depth", "1",
        ])
        data = parse_json(cp)
        stems = [n["stem"] for n in data["nodes"]]
        assert "b" in stems
        assert "c" not in stems  # depth 1 stops at b

    def test_unreachable_summary(self, tmp_path):
        vault = self._vault(tmp_path)
        _write_note(vault, "02-architecture/adr/lonely.md",
                    {"type": "adr", "slug": "lonely", "title": "Lonely"}, "")
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault), "--action", "analyze", "--seed", "lonely",
        ])
        data = parse_json(cp)
        assert data["summary"]["total_dependents"] == 0
        assert data["summary"]["unreachable"] is True

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(tmp_path), "--action", "analyze", "--seed", "x",
        ])
        assert cp.returncode == 1
