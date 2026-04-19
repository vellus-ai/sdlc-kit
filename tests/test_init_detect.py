"""Tests for sdlc-init/scripts/detect.py — project state detection.

The detect script emits a single JSON object describing the current working
directory context (git repo or not, remote URL, user config, suggested mode).

We invoke the script via `subprocess.run` so we can control the cwd — the
script relies on `Path.cwd()` and on `git` inspecting the current working
directory. All tests run inside an isolated `tmp_path` so they cannot leak
into (or be influenced by) the plugin repo's own git state.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "plugins" / "core" / "skills" / "sdlc-init" / "scripts" / "detect.py"


def _run_detect(cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Invoke detect.py with cwd set to `cwd`. Returns the CompletedProcess.

    Pass `env` to override environment variables (e.g. GIT_CONFIG_GLOBAL to
    isolate from the user's real global git config).
    """
    assert SCRIPT.exists(), f"missing script: {SCRIPT}"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd),
        env=env,
    )


def _isolated_git_env(tmp_path: Path) -> dict[str, str]:
    """Build an env dict that detaches git from any global/system config.

    This lets us simulate edge cases (missing user.email, no remote) that
    would otherwise inherit from the developer's `~/.gitconfig`.
    """
    import os
    env = os.environ.copy()
    empty_cfg = tmp_path / "_empty.gitconfig"
    empty_cfg.write_text("", encoding="utf-8")
    # `/dev/null` + an empty file both work as "no-config sentinel". We use an
    # empty file because it's cross-platform (Windows has no /dev/null).
    env["GIT_CONFIG_GLOBAL"] = str(empty_cfg)
    env["GIT_CONFIG_SYSTEM"] = str(empty_cfg)
    return env


def _parse_payload(cp: subprocess.CompletedProcess) -> dict:
    assert cp.returncode == 0, f"detect exited non-zero; stderr={cp.stderr!r}"
    assert cp.stdout.strip(), f"empty stdout; stderr={cp.stderr!r}"
    return json.loads(cp.stdout)


def _git(cwd: Path, *args: str) -> None:
    """Run a git command inside cwd; raises on failure."""
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


class TestDetectOutputShape:
    """Validate the JSON contract regardless of environment."""

    REQUIRED_FIELDS = {
        "cwd",
        "is_git_repo",
        "repo_root",
        "basename",
        "git_user_name",
        "git_user_email",
        "owner_display",
        "remote_url",
        "remote_https_url",
        "has_commits",
        "commit_count",
        "has_sdlc",
        "gh_cli_available",
        "suggested_mode",
    }

    def test_output_is_valid_json_with_all_fields(self, tmp_path):
        # Bare directory (not a git repo) should still emit a full payload.
        cp = _run_detect(tmp_path)
        data = _parse_payload(cp)
        assert self.REQUIRED_FIELDS.issubset(data.keys())

    def test_field_types(self, tmp_path):
        cp = _run_detect(tmp_path)
        data = _parse_payload(cp)
        assert isinstance(data["is_git_repo"], bool)
        assert isinstance(data["has_commits"], bool)
        assert isinstance(data["has_sdlc"], bool)
        assert isinstance(data["gh_cli_available"], bool)
        assert isinstance(data["commit_count"], int)
        assert isinstance(data["cwd"], str)
        assert isinstance(data["repo_root"], str)
        assert isinstance(data["basename"], str)
        assert data["suggested_mode"] in {"brownfield", "greenfield", "re-init"}


class TestDetectOutsideGit:
    """When cwd is not inside any git repo, detection must degrade gracefully."""

    def test_suggests_greenfield_when_no_git(self, tmp_path):
        # Create a child directory that is *not* a git repo (tmp_path itself
        # isn't initialised).
        work = tmp_path / "fresh-project"
        work.mkdir()
        cp = _run_detect(work)
        data = _parse_payload(cp)
        assert data["is_git_repo"] is False
        assert data["has_commits"] is False
        assert data["commit_count"] == 0
        assert data["remote_url"] == ""
        assert data["remote_https_url"] == ""
        assert data["suggested_mode"] == "greenfield"
        # repo_root falls back to cwd when outside a repo
        assert Path(data["repo_root"]).resolve() == work.resolve()
        assert data["basename"] == "fresh-project"


class TestDetectInsideGit:
    """When cwd is inside a real git repo, the script must surface git context."""

    def _init_repo(self, path: Path, *, remote: str | None = None,
                   user: tuple[str, str] | None = None,
                   commit: bool = False) -> None:
        _git(path, "init", "-q", "-b", "main")
        if user is not None:
            _git(path, "config", "user.name", user[0])
            _git(path, "config", "user.email", user[1])
        if remote is not None:
            _git(path, "remote", "add", "origin", remote)
        if commit:
            # We must have *some* user config to commit — set a dummy if the
            # test hasn't provided one.
            if user is None:
                _git(path, "config", "user.email", "t@example.com")
                _git(path, "config", "user.name", "Tester")
            (path / "README.md").write_text("# test\n", encoding="utf-8")
            _git(path, "add", "README.md")
            # Disable GPG signing locally — some CI envs enforce it globally.
            _git(path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")

    def test_detects_git_repo_without_commits(self, tmp_path):
        project = tmp_path / "empty-repo"
        project.mkdir()
        self._init_repo(project)
        cp = _run_detect(project)
        data = _parse_payload(cp)
        assert data["is_git_repo"] is True
        assert data["has_commits"] is False
        assert data["commit_count"] == 0
        # No commits, no .sdlc -> greenfield.
        assert data["suggested_mode"] == "greenfield"
        assert Path(data["repo_root"]).resolve() == project.resolve()

    def test_detects_remote_ssh_and_normalizes_to_https(self, tmp_path):
        project = tmp_path / "with-remote"
        project.mkdir()
        self._init_repo(
            project,
            remote="git@github.com:vellus-ai/sdlc-kit.git",
            user=("Milton", "milton@example.com"),
            commit=True,
        )
        cp = _run_detect(project)
        data = _parse_payload(cp)
        assert data["is_git_repo"] is True
        assert data["remote_url"] == "git@github.com:vellus-ai/sdlc-kit.git"
        assert data["remote_https_url"] == "https://github.com/vellus-ai/sdlc-kit"
        assert data["git_user_name"] == "Milton"
        assert data["git_user_email"] == "milton@example.com"
        assert data["owner_display"] == "Milton <milton@example.com>"
        assert data["has_commits"] is True
        assert data["commit_count"] >= 1
        # Repo with commits and no .sdlc -> brownfield.
        assert data["suggested_mode"] == "brownfield"

    def test_owner_display_combines_name_and_email(self, tmp_path):
        # `git config user.*` inherits from the global config when the local
        # repo doesn't override it, so we can't reliably simulate an
        # email-less repo without mutating the user's global config. Instead,
        # we verify the positive case: both values set produce the expected
        # "Name <email>" display string.
        project = tmp_path / "owner-repo"
        project.mkdir()
        _git(project, "init", "-q", "-b", "main")
        _git(project, "config", "user.name", "SoloName")
        _git(project, "config", "user.email", "solo@example.com")
        cp = _run_detect(project)
        data = _parse_payload(cp)
        assert data["git_user_name"] == "SoloName"
        assert data["git_user_email"] == "solo@example.com"
        assert data["owner_display"] == "SoloName <solo@example.com>"

    def test_owner_display_name_only_when_email_missing(self, tmp_path):
        # Isolate from the developer's global gitconfig so `user.email` is
        # genuinely unset.
        project = tmp_path / "name-only"
        project.mkdir()
        env = _isolated_git_env(tmp_path)
        subprocess.run(
            ["git", "init", "-q", "-b", "main"], cwd=str(project),
            env=env, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "SoloName"], cwd=str(project),
            env=env, check=True, capture_output=True, text=True,
        )
        cp = _run_detect(project, env=env)
        data = _parse_payload(cp)
        assert data["git_user_name"] == "SoloName"
        assert data["git_user_email"] == ""
        assert data["owner_display"] == "SoloName"

    def test_normalizes_ssh_protocol_remote(self, tmp_path):
        """`ssh://git@host/org/repo.git` has its own branch in _normalize_remote."""
        project = tmp_path / "ssh-proto"
        project.mkdir()
        self._init_repo(
            project,
            remote="ssh://git@gitlab.example.com/group/sub/project.git",
            user=("Milton", "milton@example.com"),
        )
        cp = _run_detect(project)
        data = _parse_payload(cp)
        assert data["remote_url"] == "ssh://git@gitlab.example.com/group/sub/project.git"
        assert data["remote_https_url"] == "https://gitlab.example.com/group/sub/project"

    def test_suggests_reinit_when_sdlc_present(self, tmp_path):
        project = tmp_path / "already-has-sdlc"
        project.mkdir()
        self._init_repo(
            project,
            user=("Milton", "milton@example.com"),
            commit=True,
        )
        # Simulate a previous scaffold.
        (project / ".sdlc").mkdir()
        cp = _run_detect(project)
        data = _parse_payload(cp)
        assert data["has_sdlc"] is True
        assert data["suggested_mode"] == "re-init"


class TestDetectExitCode:
    def test_always_exits_zero(self, tmp_path):
        # The script contract is: always exit 0 — failures are fields, not raises.
        cp = _run_detect(tmp_path)
        assert cp.returncode == 0
