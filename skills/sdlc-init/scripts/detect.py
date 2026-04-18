#!/usr/bin/env python3
"""Detect project state before SDLC Kit scaffold.

Emits a single JSON object on stdout so the sdlc-init skill can skip
redundant questions during onboarding.

Output fields:
    cwd                 : current working directory
    is_git_repo         : bool
    repo_root           : absolute path (falls back to cwd)
    basename            : name of the repo root / cwd
    git_user_name       : from `git config user.name`
    git_user_email      : from `git config user.email`
    owner_display       : "Name <email>" or "Name" or ""
    remote_url          : raw `git remote get-url origin` output
    remote_https_url    : normalized https URL (best-effort)
    has_commits         : bool
    commit_count        : int
    has_sdlc            : bool (is `<repo_root>/.sdlc` a directory?)
    gh_cli_available    : bool (is `gh` on PATH?)
    suggested_mode      : "brownfield" | "greenfield" | "re-init"

Exit codes:
    0 — always (failures are surfaced as fields, never raised)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, check=False
        )
        return r.returncode, r.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def _normalize_remote(url: str) -> str:
    """Best-effort normalize to an https URL for display."""
    if not url:
        return ""
    if url.startswith("git@"):
        host, _, rest = url[4:].partition(":")
        return f"https://{host}/{rest.removesuffix('.git')}"
    if url.startswith("ssh://git@"):
        rest = url[len("ssh://git@"):]
        host, _, path = rest.partition("/")
        return f"https://{host}/{path.removesuffix('.git')}"
    return url.removesuffix(".git")


def main() -> None:
    cwd = Path.cwd().resolve()

    rc, toplevel = _run(["git", "rev-parse", "--show-toplevel"])
    is_git_repo = rc == 0 and bool(toplevel)
    repo_root = Path(toplevel).resolve() if is_git_repo else cwd

    basename = repo_root.name

    git_user_name = ""
    git_user_email = ""
    remote_url = ""
    remote_https_url = ""
    commit_count = 0
    has_commits = False
    has_sdlc = False

    if is_git_repo:
        _, git_user_name = _run(["git", "config", "user.name"])
        _, git_user_email = _run(["git", "config", "user.email"])
        _, remote_url = _run(["git", "remote", "get-url", "origin"])
        remote_https_url = _normalize_remote(remote_url)
        rc_cnt, count_str = _run(["git", "rev-list", "--count", "HEAD"])
        if rc_cnt == 0 and count_str.isdigit():
            commit_count = int(count_str)
            has_commits = commit_count > 0
        has_sdlc = (repo_root / ".sdlc").is_dir()

    gh_cli_available = shutil.which("gh") is not None

    if has_sdlc:
        suggested_mode = "re-init"
    elif is_git_repo and has_commits:
        suggested_mode = "brownfield"
    else:
        suggested_mode = "greenfield"

    owner_display = ""
    if git_user_name and git_user_email:
        owner_display = f"{git_user_name} <{git_user_email}>"
    elif git_user_name:
        owner_display = git_user_name

    payload = {
        "cwd": str(cwd),
        "is_git_repo": is_git_repo,
        "repo_root": str(repo_root),
        "basename": basename,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
        "owner_display": owner_display,
        "remote_url": remote_url,
        "remote_https_url": remote_https_url,
        "has_commits": has_commits,
        "commit_count": commit_count,
        "has_sdlc": has_sdlc,
        "gh_cli_available": gh_cli_available,
        "suggested_mode": suggested_mode,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
