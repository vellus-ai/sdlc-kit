"""Integration tests for hooks/post-vault-write.py."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests._skill_helpers import make_vault

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "post-vault-write.py"


def _invoke_hook(vault: Path, md_path: Path, tool_name: str = "Write") -> subprocess.CompletedProcess:
    """Invoke the PostToolUse hook with the payload Claude Code sends via stdin."""
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(md_path)},
        "session_id": "test-session",
    }
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(PLUGIN_ROOT),
    )


class TestHookHappyPath:
    def test_hook_runs_on_md_inside_vault(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        md = vault / "01-planning" / "note.md"
        md.write_text("---\ntype: note\ntitle: Foo\n---\n\nBody.\n", encoding="utf-8")
        cp = _invoke_hook(vault, md)
        # Hook must not crash (exit 0 is canonical); stderr may contain warnings.
        assert cp.returncode == 0, cp.stderr

    def test_hook_skips_file_outside_vault(self, tmp_path: Path) -> None:
        # No vault marker anywhere; hook should exit gracefully.
        md = tmp_path / "random.md"
        md.write_text("no vault context\n", encoding="utf-8")
        cp = _invoke_hook(tmp_path, md)
        assert cp.returncode == 0

    def test_hook_ignores_non_md_files(self, tmp_path: Path) -> None:
        vault = make_vault(tmp_path, "01-planning")
        other = vault / "file.txt"
        other.write_text("not markdown", encoding="utf-8")
        cp = _invoke_hook(vault, other)
        # Should exit cleanly even for non-.md files.
        assert cp.returncode == 0


class TestHookResilience:
    def test_hook_handles_missing_marker(self, tmp_path: Path) -> None:
        """If the vault marker is absent, hook exits without crashing."""
        md = tmp_path / "stray.md"
        md.write_text("stray\n", encoding="utf-8")
        cp = _invoke_hook(tmp_path, md)
        assert cp.returncode == 0

    def test_hook_handles_empty_stdin(self, tmp_path: Path) -> None:
        cp = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="",
            capture_output=True,
            text=True,
            cwd=str(PLUGIN_ROOT),
        )
        # Empty stdin is malformed; hook should not crash the whole pipeline.
        assert cp.returncode in (0, 1)
