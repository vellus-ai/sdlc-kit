"""Tests for sdlc-task — Kiro task-marker manager operating on
`04-specs/<feature>/tasks.md`.

Marker convention:
    - [ ]   queued
    - [-]   in_progress       (only ONE per feature unless --allow-multi-active)
    - [x]   completed
    - [~]   needs_attention   (blocker note on the following line)

Actions exercised: list | start | complete | block | reopen.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests._skill_helpers import (
    make_vault,
    parse_json,
    run_script,
)


TASKS_FIXTURE = """---
type: spec-tasks
title: "Tasks — Demo Feature"
slug: "demo-feature"
status: draft
phase: 04
feature: "demo-feature"
---

# Tasks — Demo Feature

## Phase 1 — Setup

- [ ] **TASK-001** — Scaffold module entrypoint.
- [ ] **TASK-002** — Implement happy path for Service.Create.
- [ ] **TASK-003** — Add input validation.
"""


class TestTaskSkill:
    SCRIPT = "sdlc-task/scripts/task.py"
    FEATURE = "demo-feature"

    # ------------------------------------------------------------------
    # fixtures
    # ------------------------------------------------------------------

    def _vault(self, tmp_path: Path) -> Path:
        """Build a vault with the 04-specs phase and a minimal tasks.md
        fixture under `04-specs/<FEATURE>/tasks.md`.
        """
        vault = make_vault(tmp_path, "04-specs")
        feature_dir = vault / "04-specs" / self.FEATURE
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "tasks.md").write_text(TASKS_FIXTURE, encoding="utf-8")
        return vault

    def _tasks_path(self, vault: Path) -> Path:
        return vault / "04-specs" / self.FEATURE / "tasks.md"

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    def test_list_enumerates_every_task(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "list",
            "--feature", self.FEATURE,
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["action"] == "list"
        assert data["count"] == 3
        ids = [t["id"] for t in data["tasks"]]
        assert ids == ["TASK-001", "TASK-002", "TASK-003"]
        assert all(t["marker"] == "[ ]" for t in data["tasks"])
        assert all(t["status"] == "queued" for t in data["tasks"])

    def test_list_missing_tasks_file(self, tmp_path):
        vault = make_vault(tmp_path, "04-specs")
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "list",
            "--feature", "does-not-exist",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("tasks file not found" in e for e in data["errors"])

    def test_list_invalid_feature_slug(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "list",
            "--feature", "Bad_Slug",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid --feature" in e for e in data["errors"])

    # ------------------------------------------------------------------
    # start — queued → in_progress
    # ------------------------------------------------------------------

    def test_start_flips_queued_to_in_progress(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[ ]"
        assert data["new_marker"] == "[-]"
        assert data["previous_status"] == "queued"
        assert data["new_status"] == "in_progress"
        text = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [-] **TASK-001**" in text
        # untouched
        assert "- [ ] **TASK-002**" in text
        assert "- [ ] **TASK-003**" in text

    def test_start_refuses_second_active_without_flag(self, tmp_path):
        vault = self._vault(tmp_path)
        # Start the first task successfully.
        first = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert first.returncode == 0, first.stderr

        # Attempt to start a second task without the bypass flag.
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-002",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("already in-progress" in e for e in data["errors"])
        # File unchanged for TASK-002.
        text = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [ ] **TASK-002**" in text

    def test_start_allows_second_active_with_flag(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-002",
            "--allow-multi-active",
        ])
        assert cp.returncode == 0, cp.stderr
        text = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [-] **TASK-001**" in text
        assert "- [-] **TASK-002**" in text

    def test_start_idempotent_on_already_in_progress(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[-]"
        assert data["new_marker"] == "[-]"
        assert data["previous_status"] == "in_progress"
        assert data["new_status"] == "in_progress"

    # ------------------------------------------------------------------
    # complete — anything → completed
    # ------------------------------------------------------------------

    def test_complete_from_in_progress(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "complete",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[-]"
        assert data["new_marker"] == "[x]"
        assert data["new_status"] == "completed"
        text = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [x] **TASK-001**" in text

    def test_complete_directly_from_queued(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "complete",
            "--feature", self.FEATURE,
            "--id", "TASK-002",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[ ]"
        assert data["new_marker"] == "[x]"
        assert data["new_status"] == "completed"

    # ------------------------------------------------------------------
    # block — requires --note; writes note under the task line
    # ------------------------------------------------------------------

    def test_block_requires_note(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "block",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("requires --note" in e for e in data["errors"])

    def test_block_writes_marker_and_note(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "block",
            "--feature", self.FEATURE,
            "--id", "TASK-002",
            "--note", "waiting on schema decision",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["new_marker"] == "[~]"
        assert data["new_status"] == "needs_attention"
        text = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [~] **TASK-002**" in text
        assert "> blocked: waiting on schema decision" in text

    # ------------------------------------------------------------------
    # reopen — [x] | [~] → [ ]
    # ------------------------------------------------------------------

    def test_reopen_from_completed(self, tmp_path):
        vault = self._vault(tmp_path)
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "complete",
            "--feature", self.FEATURE,
            "--id", "TASK-003",
        ])
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "reopen",
            "--feature", self.FEATURE,
            "--id", "TASK-003",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[x]"
        assert data["new_marker"] == "[ ]"
        assert data["new_status"] == "queued"

    def test_reopen_from_blocked_strips_note(self, tmp_path):
        vault = self._vault(tmp_path)
        # First block with a note.
        run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "block",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
            "--note", "needs approval",
        ])
        text_before = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "> blocked: needs approval" in text_before

        # Now reopen — should flip back to `[ ]` AND strip the note.
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "reopen",
            "--feature", self.FEATURE,
            "--id", "TASK-001",
        ])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["previous_marker"] == "[~]"
        assert data["new_marker"] == "[ ]"
        text_after = self._tasks_path(vault).read_text(encoding="utf-8")
        assert "- [ ] **TASK-001**" in text_after
        assert "> blocked: needs approval" not in text_after

    # ------------------------------------------------------------------
    # argument validation
    # ------------------------------------------------------------------

    def test_unknown_task_id_fails(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "complete",
            "--feature", self.FEATURE,
            "--id", "TASK-999",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("TASK-999 not found" in e for e in data["errors"])

    def test_invalid_task_id_shape(self, tmp_path):
        vault = self._vault(tmp_path)
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(vault),
            "--action", "start",
            "--feature", self.FEATURE,
            "--id", "BAD-001",
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("invalid --id" in e for e in data["errors"])

    def test_not_a_vault(self, tmp_path):
        cp = run_script(self.SCRIPT, [
            "--vault-root", str(tmp_path),
            "--action", "list",
            "--feature", self.FEATURE,
        ])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert any("not a vault" in e for e in data["errors"])
