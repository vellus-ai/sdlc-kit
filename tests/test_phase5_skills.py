"""Tests for Phase 5 skills: sdlc-worktree and sdlc-retro."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
# sdlc-worktree
# ---------------------------------------------------------------------------

@pytest.fixture
def git_vault_dir(tmp_path):
    """Creates a minimal valid vault inside a directory that has a .git folder (simulated repo)."""
    git_root = tmp_path / "repo"
    git_root.mkdir()
    (git_root / ".git").mkdir()
    vault = git_root / "vault"
    vault.mkdir()
    kit = vault / ".sdlc-kit"
    kit.mkdir()
    (kit / "marker.json").write_text(json.dumps({"version": "0.1.0"}))
    return vault


class TestWorktreeSkill:
    SCRIPT = SKILLS_DIR / "sdlc-worktree" / "scripts" / "worktree.py"

    # --- create ---

    def test_create_dry_run(self, git_vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--branch", "feat/login-google",
            "--vault-root", str(git_vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["branch"] == "feat/login-google"
        assert "path" in data
        assert "git_root" in data
        assert "feat-login-google" in data["path"]

    def test_create_dry_run_with_task_id(self, git_vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--branch", "feat/login-google",
            "--task-id", "42",
            "--vault-root", str(git_vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["task_id"] == "42"

    def test_create_missing_branch(self, git_vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--vault-root", str(git_vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "--branch" in data["message"]

    def test_create_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--branch", "feat/test",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2

    def test_create_worktree_path_at_git_root(self, git_vault_dir):
        """Worktree path should be at <git_root>/.worktrees/<slug>."""
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--branch", "feat/my-feature",
            "--vault-root", str(git_vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        # Worktree should be under .worktrees/ at git root level
        assert ".worktrees" in data["path"]
        assert "feat-my-feature" in data["path"]
        # git_root should be the parent of vault
        assert str(git_vault_dir.parent) in data["git_root"]

    def test_create_slug_replaces_slash(self, git_vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--branch", "fix/bug-123",
            "--vault-root", str(git_vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "fix-bug-123" in data["path"]

    # --- list ---

    def test_list_dry_run_not_needed(self, vault_dir):
        """list action doesn't need --dry-run since it's read-only; should work fine."""
        # Mock subprocess.run to return a porcelain list
        result = run_script(self.SCRIPT, [
            "--action", "list",
            "--vault-root", str(vault_dir),
        ])
        # Should not exit 2 (vault infra error). May exit 0 or 1 depending on git availability.
        # In CI / test env, git worktree list might fail gracefully, returning empty list.
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert "worktrees" in data
        assert isinstance(data["worktrees"], list)

    def test_list_filters_feat_and_fix(self, tmp_path):
        """Unit test for list filtering logic using module import."""
        sys.path.insert(0, str(CORE_DIR))
        from core.git import parse_worktree_list

        raw = (
            "worktree /repo\nHEAD abc123\nbranch refs/heads/main\n\n"
            "worktree /repo/.worktrees/feat-login\nHEAD def456\nbranch refs/heads/feat/login\n\n"
            "worktree /repo/.worktrees/fix-crash\nHEAD ghi789\nbranch refs/heads/fix/crash\n\n"
        )
        worktrees = parse_worktree_list(raw)
        filtered = [
            wt for wt in worktrees
            if wt.get("branch") and (
                wt["branch"].startswith("feat/") or wt["branch"].startswith("fix/")
            )
        ]
        assert len(filtered) == 2
        branches = {wt["branch"] for wt in filtered}
        assert "feat/login" in branches
        assert "fix/crash" in branches
        assert "main" not in branches

    # --- close ---

    def test_close_dry_run_branch_not_found(self, git_vault_dir):
        """close --dry-run with a branch not in worktree list exits 1 (branch not found)."""
        result = run_script(self.SCRIPT, [
            "--action", "close",
            "--branch", "feat/login-google",
            "--vault-root", str(git_vault_dir),
            "--dry-run",
        ])
        # Branch not found in git worktree list => error
        assert result.stdout.strip()
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert result.returncode == 1

    def test_close_missing_branch(self, git_vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "close",
            "--vault-root", str(git_vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "--branch" in data["message"]

    # --- sync ---

    def test_sync_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "sync",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"

    def test_sync_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "sync",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# sdlc-retro
# ---------------------------------------------------------------------------

class TestRetroSkill:
    SCRIPT = SKILLS_DIR / "sdlc-retro" / "scripts" / "retro.py"

    # --- create ---

    def test_create_dry_run(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "Sprint 23",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["sprint"] == "Sprint 23"
        assert data["slug"] == "sprint-23"
        assert data["file"] == "retro-sprint-23.md"
        # File must NOT be created
        assert not (vault_dir / "07-retrospectives" / "retro-sprint-23.md").exists()

    def test_create_creates_file(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "Sprint 23",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["file"] == "retro-sprint-23.md"

        retro_path = vault_dir / "07-retrospectives" / "retro-sprint-23.md"
        assert retro_path.exists()

    def test_create_frontmatter(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "Sprint 23",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "07-retrospectives" / "retro-sprint-23.md").read_text(encoding="utf-8")
        assert 'title: "Retro: Sprint 23"' in content
        assert "type: retrospective" in content
        assert "status: draft" in content
        assert 'phase: "07"' in content

    def test_create_template_sections(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "Sprint 23",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "07-retrospectives" / "retro-sprint-23.md").read_text(encoding="utf-8")
        assert "## O que foi bem" in content
        assert "## O que pode melhorar" in content
        assert "## Itens de ação" in content
        assert "## Próximos passos" in content

    def test_create_duplicate_exits_1(self, vault_dir):
        args = [
            "--action", "create",
            "--sprint", "Sprint 23",
            "--vault-root", str(vault_dir),
        ]
        run_script(self.SCRIPT, args)
        result = run_script(self.SCRIPT, args)
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "already exists" in data["message"]

    def test_create_slug_from_date_sprint(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "2026-04",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["file"] == "retro-2026-04.md"

    def test_create_missing_sprint(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"

    def test_create_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "create",
            "--sprint", "Sprint 1",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2

    # --- list ---

    def test_list_empty_when_dir_missing(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "list",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["retros"] == []

    def test_list_returns_retros(self, vault_dir):
        # Create two retros
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 1", "--vault-root", str(vault_dir),
        ])
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 2", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "list",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert len(data["retros"]) == 2
        files = {r["file"] for r in data["retros"]}
        assert "retro-sprint-1.md" in files
        assert "retro-sprint-2.md" in files

    def test_list_includes_title_and_status(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 5", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "list",
            "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        retro = data["retros"][0]
        assert retro["title"] == "Retro: Sprint 5"
        assert retro["status"] == "draft"

    def test_list_ignores_non_retro_files(self, vault_dir):
        retro_dir = vault_dir / "07-retrospectives"
        retro_dir.mkdir(parents=True, exist_ok=True)
        # A file that doesn't match retro-*.md
        (retro_dir / "README.md").write_text("# readme\n", encoding="utf-8")
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 7", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "list", "--vault-root", str(vault_dir),
        ])
        data = json.loads(result.stdout)
        files = {r["file"] for r in data["retros"]}
        assert "README.md" not in files
        assert "retro-sprint-7.md" in files

    def test_list_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "list",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2

    # --- add-action ---

    def test_add_action_dry_run(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 10", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Improve CI pipeline",
            "--retro-file", "retro-sprint-10.md",
            "--vault-root", str(vault_dir),
            "--dry-run",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry-run"
        assert data["action_item"] == "Improve CI pipeline"
        # File should NOT be modified
        content = (vault_dir / "07-retrospectives" / "retro-sprint-10.md").read_text(encoding="utf-8")
        assert "Improve CI pipeline" not in content

    def test_add_action_appends_item(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 10", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Improve CI pipeline",
            "--retro-file", "retro-sprint-10.md",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["action_item"] == "Improve CI pipeline"

        content = (vault_dir / "07-retrospectives" / "retro-sprint-10.md").read_text(encoding="utf-8")
        assert "- [ ] Improve CI pipeline" in content

    def test_add_action_multiple_items(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 11", "--vault-root", str(vault_dir),
        ])
        for item in ["Action A", "Action B", "Action C"]:
            run_script(self.SCRIPT, [
                "--action", "add-action",
                "--action-item", item,
                "--retro-file", "retro-sprint-11.md",
                "--vault-root", str(vault_dir),
            ])
        content = (vault_dir / "07-retrospectives" / "retro-sprint-11.md").read_text(encoding="utf-8")
        assert "- [ ] Action A" in content
        assert "- [ ] Action B" in content
        assert "- [ ] Action C" in content

    def test_add_action_item_in_correct_section(self, vault_dir):
        """Action item must be inside ## Itens de ação, not after ## Próximos passos."""
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 12", "--vault-root", str(vault_dir),
        ])
        run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Fix deployment process",
            "--retro-file", "retro-sprint-12.md",
            "--vault-root", str(vault_dir),
        ])
        content = (vault_dir / "07-retrospectives" / "retro-sprint-12.md").read_text(encoding="utf-8")
        itens_idx = content.index("## Itens de ação")
        proximos_idx = content.index("## Próximos passos")
        item_idx = content.index("- [ ] Fix deployment process")
        assert itens_idx < item_idx < proximos_idx

    def test_add_action_missing_retro_file(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Do something",
            "--retro-file", "retro-nonexistent.md",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "not found" in data["message"]

    def test_add_action_missing_action_item(self, vault_dir):
        run_script(self.SCRIPT, [
            "--action", "create", "--sprint", "Sprint 13", "--vault-root", str(vault_dir),
        ])
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--retro-file", "retro-sprint-13.md",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"

    def test_add_action_missing_retro_file_arg(self, vault_dir):
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Do something",
            "--vault-root", str(vault_dir),
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "error"

    def test_add_action_missing_vault(self, tmp_path):
        result = run_script(self.SCRIPT, [
            "--action", "add-action",
            "--action-item", "Do something",
            "--retro-file", "retro-sprint-1.md",
            "--vault-root", str(tmp_path),
        ])
        assert result.returncode == 2
