"""Tests for Phase 4 skills: domain, c4, design-system, trace, impact."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
CORE_DIR = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_script(script_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script_path)] + args,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# sdlc-domain
# ---------------------------------------------------------------------------

class TestDomainSkill:
    SCRIPT = SKILLS_DIR / "sdlc-domain" / "scripts" / "domain.py"

    def test_create_context_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create-context",
            "--context-name", "Order Management",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["slug"] == "order-management"
        assert len(data["files"]) == 2

    def test_create_context_creates_files(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create-context",
            "--context-name", "Order Management",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert len(data["created"]) == 2

        context_dir = vault_dir / "04-domain" / "order-management"
        assert (context_dir / "context-map.md").exists()
        assert (context_dir / "ubiquitous-language.md").exists()

    def test_create_context_idempotent(self, vault_dir):
        args = [
            "--action", "create-context",
            "--context-name", "Order Management",
            "--vault-root", str(vault_dir),
        ]
        run_script(self.SCRIPT, args)
        result = run_script(self.SCRIPT, args)
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        # Second run: nothing created (files already exist)
        assert data["created"] == []

    def test_create_context_frontmatter(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create-context",
            "--context-name", "Payments",
            "--vault-root", str(vault_dir),
        ])
        context_map = (vault_dir / "04-domain" / "payments" / "context-map.md").read_text()
        assert "type: context-map" in context_map
        assert "status: draft" in context_map
        assert 'phase: "04"' in context_map

    def test_add_event_creates_file(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-event",
            "--context-name", "Orders",
            "--event-name", "OrderPlaced",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"

        events_file = vault_dir / "04-domain" / "orders" / "domain-events.md"
        assert events_file.exists()
        content = events_file.read_text()
        assert "## OrderPlaced" in content
        assert "**Trigger:**" in content
        assert "**Payload:**" in content

    def test_add_event_appends(self, vault_dir):
        base_args = ["--action", "add-event", "--context-name", "Orders", "--vault-root", str(vault_dir)]
        run_script(self.SCRIPT, base_args + ["--event-name", "OrderPlaced"])
        run_script(self.SCRIPT, base_args + ["--event-name", "OrderCancelled"])

        content = (vault_dir / "04-domain" / "orders" / "domain-events.md").read_text()
        assert "## OrderPlaced" in content
        assert "## OrderCancelled" in content

    def test_add_event_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-event",
            "--context-name", "Orders",
            "--event-name", "OrderPlaced",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        # File should NOT be created
        assert not (vault_dir / "04-domain" / "orders" / "domain-events.md").exists()

    def test_list_contexts_empty(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "list-contexts",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["contexts"] == []

    def test_list_contexts_excludes_templates(self, vault_dir):
        (vault_dir / "04-domain" / "_templates").mkdir(parents=True)
        (vault_dir / "04-domain" / "payments").mkdir(parents=True)
        result = run_script(self.SCRIPT, [
            "--action", "list-contexts",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        assert "_templates" not in data["contexts"]
        assert "payments" in data["contexts"]

    def test_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "list-contexts",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2

    def test_create_context_missing_name(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create-context",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1

    def test_slugify_special_chars(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create-context",
            "--context-name", "User Auth & Session",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["slug"] == "user-auth--session"


# ---------------------------------------------------------------------------
# sdlc-c4
# ---------------------------------------------------------------------------

class TestC4Skill:
    SCRIPT = SKILLS_DIR / "sdlc-c4" / "scripts" / "c4.py"

    @pytest.mark.parametrize("level", ["context", "container", "component"])
    def test_create_diagram_dry_run(self, vault_dir, level):
        result = run_script(self.SCRIPT, [
            "--level", level,
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["level"] == level

    @pytest.mark.parametrize("level", ["context", "container", "component"])
    def test_create_diagram_creates_file(self, vault_dir, level):
        result = run_script(self.SCRIPT, [
            "--level", level,
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"

        dest = vault_dir / "02-architecture" / f"c4-{level}-my-platform.md"
        assert dest.exists()

    def test_create_diagram_frontmatter(self, vault_dir):
        run_script(self.SCRIPT, [
            "--level", "context",
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "02-architecture" / "c4-context-my-platform.md").read_text()
        assert "type: c4-diagram" in content
        assert "level: context" in content
        assert "status: draft" in content
        assert 'phase: "02"' in content

    def test_create_diagram_contains_mermaid(self, vault_dir):
        run_script(self.SCRIPT, [
            "--level", "context",
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "02-architecture" / "c4-context-my-platform.md").read_text()
        assert "```mermaid" in content
        assert "C4Context" in content

    def test_container_diagram_mermaid(self, vault_dir):
        run_script(self.SCRIPT, [
            "--level", "container",
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "02-architecture" / "c4-container-my-platform.md").read_text()
        assert "C4Container" in content

    def test_component_diagram_mermaid(self, vault_dir):
        run_script(self.SCRIPT, [
            "--level", "component",
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "02-architecture" / "c4-component-my-platform.md").read_text()
        assert "C4Component" in content

    def test_duplicate_diagram_exits_1(self, vault_dir):
        args = [
            "--level", "context",
            "--system-name", "My Platform",
            "--vault-root", str(vault_dir),
        ]
        run_script(self.SCRIPT, args)
        result = run_script(self.SCRIPT, args)
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "already exists" in data["message"]

    def test_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--level", "context",
            "--system-name", "Test",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# sdlc-design-system
# ---------------------------------------------------------------------------

class TestDesignSystemSkill:
    SCRIPT = SKILLS_DIR / "sdlc-design-system" / "scripts" / "design_system.py"

    def test_init_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "init",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert "tokens.md" in data["files"]

    def test_init_creates_files(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "init",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert "tokens.md" in data["created"]
        assert "components.md" in data["created"]
        assert "patterns.md" in data["created"]

        assert (vault_dir / "06-design-system" / "tokens.md").exists()
        assert (vault_dir / "06-design-system" / "components.md").exists()
        assert (vault_dir / "06-design-system" / "patterns.md").exists()

    def test_init_idempotent(self, vault_dir):
        run_script(self.SCRIPT, ["--action", "init", "--vault-root", str(vault_dir)])
        result = run_script(self.SCRIPT, ["--action", "init", "--vault-root", str(vault_dir)])
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["created"] == []
        assert set(data["skipped"]) == {"tokens.md", "components.md", "patterns.md"}

    def test_init_frontmatter(self, vault_dir):
        run_script(self.SCRIPT, ["--action", "init", "--vault-root", str(vault_dir)])
        content = (vault_dir / "06-design-system" / "tokens.md").read_text()
        assert "type: design-tokens" in content
        assert "status: draft" in content
        assert 'phase: "06"' in content

    def test_add_token_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-token",
            "--name", "primary-color",
            "--category", "color",
            "--value", "#1A73E8",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert not (vault_dir / "06-design-system" / "tokens.md").exists()

    def test_add_token_appends_row(self, vault_dir):
        run_script(self.SCRIPT, ["--action", "init", "--vault-root", str(vault_dir)])
        run_script(self.SCRIPT, [
            "--action", "add-token",
            "--name", "primary-color",
            "--category", "color",
            "--value", "#1A73E8",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "06-design-system" / "tokens.md").read_text()
        assert "| primary-color | color | #1A73E8 |" in content

    def test_add_token_creates_tokens_if_missing(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-token",
            "--name", "spacing-sm",
            "--category", "spacing",
            "--value", "8px",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        assert (vault_dir / "06-design-system" / "tokens.md").exists()

    def test_add_token_missing_args(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-token",
            "--name", "primary-color",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1

    def test_add_component_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-component",
            "--name", "Button",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"

    def test_add_component_appends_entry(self, vault_dir):
        run_script(self.SCRIPT, ["--action", "init", "--vault-root", str(vault_dir)])
        run_script(self.SCRIPT, [
            "--action", "add-component",
            "--name", "Button",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "06-design-system" / "components.md").read_text()
        assert "## Button" in content
        assert "**Status:** draft" in content

    def test_add_component_missing_name(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-component",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1

    def test_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "init",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# sdlc-trace
# ---------------------------------------------------------------------------

class TestTraceSkill:
    SCRIPT = SKILLS_DIR / "sdlc-trace" / "scripts" / "trace.py"

    def _setup_spec(self, vault_dir: Path, slug: str = "my-feature"):
        spec_dir = vault_dir / "03-development" / slug
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "requirements.md").write_text(
            "# Requirements\n\n"
            "The system SHALL validate user input.\n"
            "WHEN the user submits a form, the system SHALL check all required fields.\n"
            "The system SHALL return an error if validation fails.\n",
            encoding="utf-8",
        )
        (spec_dir / "design.md").write_text("# Design\n\nSee architecture docs.\n", encoding="utf-8")
        (spec_dir / "tasks.md").write_text(
            "# Tasks\n\n"
            "- [ ] Implement form validation\n"
            "- [x] Write unit tests\n"
            "- [ ] Add error messages\n",
            encoding="utf-8",
        )
        return spec_dir

    def test_trace_dry_run(self, vault_dir):
        self._setup_spec(vault_dir)
        result = run_script(self.SCRIPT, [
            "--spec-slug", "my-feature",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["requirements_found"] == 3
        assert not (vault_dir / "03-development" / "my-feature" / "traceability.md").exists()

    def test_trace_creates_file(self, vault_dir):
        self._setup_spec(vault_dir)
        result = run_script(self.SCRIPT, [
            "--spec-slug", "my-feature",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["requirements_found"] == 3
        assert data["tasks_found"] == 3

        trace_path = vault_dir / "03-development" / "my-feature" / "traceability.md"
        assert trace_path.exists()

    def test_trace_table_content(self, vault_dir):
        self._setup_spec(vault_dir)
        run_script(self.SCRIPT, [
            "--spec-slug", "my-feature",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "03-development" / "my-feature" / "traceability.md").read_text()
        assert "| Requirement | Design Ref | Task | Status |" in content
        assert "SHALL" in content
        assert "design.md" in content
        assert "open" in content

    def test_trace_frontmatter(self, vault_dir):
        self._setup_spec(vault_dir)
        run_script(self.SCRIPT, [
            "--spec-slug", "my-feature",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "03-development" / "my-feature" / "traceability.md").read_text()
        assert "type: traceability" in content
        assert 'phase: "03"' in content

    def test_trace_missing_spec_dir(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--spec-slug", "nonexistent",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"

    def test_trace_missing_requirements(self, vault_dir):
        spec_dir = vault_dir / "03-development" / "no-reqs"
        spec_dir.mkdir(parents=True)
        result = run_script(self.SCRIPT, [
            "--spec-slug", "no-reqs",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "requirements.md" in data["message"]

    def test_trace_no_tasks_file(self, vault_dir):
        spec_dir = vault_dir / "03-development" / "no-tasks"
        spec_dir.mkdir(parents=True)
        (spec_dir / "requirements.md").write_text(
            "The system SHALL do something.\n", encoding="utf-8"
        )
        result = run_script(self.SCRIPT, [
            "--spec-slug", "no-tasks",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["tasks_found"] == 0

    def test_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--spec-slug", "anything",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# sdlc-impact
# ---------------------------------------------------------------------------

class TestImpactSkill:
    SCRIPT = SKILLS_DIR / "sdlc-impact" / "scripts" / "impact.py"

    def _setup_vault_docs(self, vault_dir: Path):
        (vault_dir / "01-planning").mkdir(parents=True, exist_ok=True)
        (vault_dir / "01-planning" / "roadmap.md").write_text(
            "# Roadmap\n\nWe plan to implement OrderService this quarter.\n"
            "OrderService will handle all order processing.\n",
            encoding="utf-8",
        )
        (vault_dir / "02-architecture").mkdir(parents=True, exist_ok=True)
        (vault_dir / "02-architecture" / "overview.md").write_text(
            "# Architecture\n\nOrderService is the core domain service.\n",
            encoding="utf-8",
        )
        # Internal file — should be excluded
        sdlc_dir = vault_dir / ".sdlc-kit"
        (sdlc_dir / "internal.md").write_text(
            "OrderService internal notes\n", encoding="utf-8"
        )

    def test_impact_dry_run(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "OrderService",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["term"] == "OrderService"

    def test_impact_finds_matches(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "OrderService",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["term"] == "OrderService"
        assert data["total_files"] == 2

    def test_impact_match_structure(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "OrderService",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        for match in data["matches"]:
            assert "file" in match
            assert "count" in match
            assert "snippet" in match
            assert len(match["snippet"]) <= 100

    def test_impact_case_insensitive(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "orderservice",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        assert data["total_files"] == 2

    def test_impact_excludes_sdlc_kit(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "OrderService",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        file_paths = [m["file"] for m in data["matches"]]
        assert not any(".sdlc-kit" in p for p in file_paths)

    def test_impact_no_matches(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "NonExistentConcept99999",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["total_files"] == 0
        assert data["matches"] == []

    def test_impact_count_occurrences(self, vault_dir):
        self._setup_vault_docs(vault_dir)
        result = run_script(self.SCRIPT, [
            "--term", "OrderService",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        roadmap_match = next(
            (m for m in data["matches"] if "roadmap" in m["file"]), None
        )
        assert roadmap_match is not None
        assert roadmap_match["count"] == 2  # appears on 2 lines in roadmap.md

    def test_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--term", "anything",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2
