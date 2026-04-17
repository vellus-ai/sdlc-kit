# core/git.py
import json
import sqlite3
import subprocess
from pathlib import Path

def parse_worktree_list(raw: str) -> list[dict]:
    """Parse output of `git worktree list --porcelain`."""
    worktrees = []
    current: dict = {}
    for line in raw.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[9:], "branch": None, "head": None}
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            ref = line[7:]
            current["branch"] = ref.removeprefix("refs/heads/")
    if current:
        worktrees.append(current)
    return worktrees

def parse_pr_list(raw: str) -> dict[str, dict]:
    """Parse output of `gh pr list --json number,headRefName,state,url`."""
    prs: dict[str, dict] = {}
    for item in json.loads(raw):
        branch = item["headRefName"]
        prs[branch] = {
            "pr_number": item["number"],
            "pr_status": item["state"].lower(),
            "pr_url": item["url"],
        }
    return prs

def sync_worktrees(vault_root: Path, conn: sqlite3.Connection) -> dict:
    """Sync git worktrees and PR status into the worktrees table."""
    try:
        wt_raw = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(vault_root.parent),
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"error": "git not available"}

    worktrees = parse_worktree_list(wt_raw)

    pr_map: dict = {}
    try:
        pr_raw = subprocess.check_output(
            ["gh", "pr", "list", "--json", "number,headRefName,state,url", "--state", "all"],
            cwd=str(vault_root.parent),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        pr_map = parse_pr_list(pr_raw)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    synced = 0
    for wt in worktrees:
        branch = wt["branch"]
        if not branch or not (branch.startswith("feat/") or branch.startswith("fix/")):
            continue
        pr = pr_map.get(branch, {})
        conn.execute(
            """
            INSERT INTO worktrees (branch, path, status, pr_number, pr_status, pr_url)
            VALUES (?, ?, 'active', ?, ?, ?)
            ON CONFLICT(branch) DO UPDATE SET
                path=excluded.path,
                pr_number=excluded.pr_number,
                pr_status=excluded.pr_status,
                pr_url=excluded.pr_url
            """,
            (branch, wt["path"], pr.get("pr_number"), pr.get("pr_status"), pr.get("pr_url")),
        )
        synced += 1

    conn.commit()
    return {"synced": synced}
