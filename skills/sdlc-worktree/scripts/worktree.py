#!/usr/bin/env python3
"""Manage git worktrees with SDLC Kit integration."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _slugify(branch: str) -> str:
    slug = branch.replace("/", "-")
    return re.sub(r"[^a-z0-9-]", "", slug.lower())


def _find_git_root(start: Path) -> Path | None:
    """Walk up from start looking for .git directory."""
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _get_worktree_list() -> list[dict]:
    """Run git worktree list --porcelain and return parsed result."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.git import parse_worktree_list
    return parse_worktree_list(result.stdout)


def action_create(args) -> None:
    if not args.branch:
        print(json.dumps({"status": "error", "message": "--branch is required for create"}))
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root

    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    git_root = _find_git_root(vault)
    if not git_root:
        print(json.dumps({"status": "error", "message": "git repository not found"}))
        sys.exit(2)

    slug = _slugify(args.branch)
    wt_path = git_root / ".worktrees" / slug

    if args.dry_run:
        out = {
            "status": "dry-run",
            "branch": args.branch,
            "path": str(wt_path),
            "git_root": str(git_root),
        }
        if args.task_id:
            out["task_id"] = args.task_id
        print(json.dumps(out))
        return

    result = subprocess.run(
        ["git", "worktree", "add", str(wt_path), "-b", args.branch],
        capture_output=True,
        text=True,
        cwd=str(git_root),
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "git worktree add failed"
        print(json.dumps({"status": "error", "message": msg}))
        sys.exit(1)

    out = {
        "status": "ok",
        "branch": args.branch,
        "path": str(wt_path),
        "git_root": str(git_root),
    }
    if args.task_id:
        out["task_id"] = args.task_id
    print(json.dumps(out))


def action_list(args) -> None:
    worktrees = _get_worktree_list()
    filtered = [
        wt for wt in worktrees
        if wt.get("branch") and (
            wt["branch"].startswith("feat/") or wt["branch"].startswith("fix/")
        )
    ]
    print(json.dumps({"status": "ok", "worktrees": filtered}))


def action_close(args) -> None:
    if not args.branch:
        print(json.dumps({"status": "error", "message": "--branch is required for close"}))
        sys.exit(1)

    worktrees = _get_worktree_list()
    target = next((wt for wt in worktrees if wt.get("branch") == args.branch), None)
    if not target:
        print(json.dumps({"status": "error", "message": f"worktree for branch '{args.branch}' not found"}))
        sys.exit(1)

    wt_path = target["path"]

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "branch": args.branch, "path": wt_path}))
        return

    result = subprocess.run(
        ["git", "worktree", "remove", wt_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "git worktree remove failed"
        # Check for uncommitted changes
        if "uncommitted" in msg.lower() or "untracked" in msg.lower() or "dirty" in msg.lower():
            print(json.dumps({"status": "error", "message": f"worktree has uncommitted changes: {msg}"}))
        else:
            print(json.dumps({"status": "error", "message": msg}))
        sys.exit(1)

    print(json.dumps({"status": "ok", "branch": args.branch, "removed_path": wt_path}))


def action_sync(args) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root, get_db_path
    from core.db import connect
    from core.git import sync_worktrees

    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "message": "sync would update worktrees table"}))
        return

    conn = connect(get_db_path(vault))
    result = sync_worktrees(vault, conn)
    conn.close()
    result["status"] = "ok"
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["create", "list", "close", "sync"], default="list")
    parser.add_argument("--branch", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.action == "create":
        action_create(args)
    elif args.action == "list":
        action_list(args)
    elif args.action == "close":
        action_close(args)
    elif args.action == "sync":
        action_sync(args)
    else:
        print(json.dumps({"status": "error", "message": f"unknown action: {args.action}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
