# tests/test_git.py
import json

from core.git import parse_pr_list, parse_worktree_list


def test_parse_worktree_list_basic():
    raw = (
        "worktree /home/user/project\n"
        "HEAD abc123\n"
        "branch refs/heads/feat/login\n"
        "\n"
        "worktree /home/user/project/.git/worktrees/feat-billing\n"
        "HEAD def456\n"
        "branch refs/heads/feat/billing\n"
        "\n"
    )
    result = parse_worktree_list(raw)
    assert len(result) == 2
    assert result[0]["branch"] == "feat/login"
    assert result[1]["branch"] == "feat/billing"

def test_parse_worktree_list_no_branch():
    raw = "worktree /home/user/project\nHEAD abc123\n\n"
    result = parse_worktree_list(raw)
    assert len(result) == 1
    assert result[0]["branch"] is None

def test_parse_worktree_list_main_branch():
    raw = (
        "worktree /home/user/project\n"
        "HEAD abc123\n"
        "branch refs/heads/main\n"
        "\n"
    )
    result = parse_worktree_list(raw)
    assert result[0]["branch"] == "main"

def test_parse_pr_list_basic():
    raw = json.dumps([
        {"number": 14, "headRefName": "feat/login", "state": "OPEN", "url": "https://github.com/x/y/pull/14"},
        {"number": 15, "headRefName": "feat/billing", "state": "MERGED", "url": "https://github.com/x/y/pull/15"},
        {"number": 16, "headRefName": "feat/api", "state": "CLOSED", "url": "https://github.com/x/y/pull/16"},
    ])
    result = parse_pr_list(raw)
    assert result["feat/login"]["pr_number"] == 14
    assert result["feat/login"]["pr_status"] == "open"
    assert result["feat/billing"]["pr_status"] == "merged"
    assert result["feat/api"]["pr_status"] == "closed"

def test_parse_pr_list_empty():
    result = parse_pr_list("[]")
    assert result == {}

def test_parse_pr_list_draft():
    raw = json.dumps([
        {"number": 17, "headRefName": "feat/new", "state": "OPEN", "url": "https://github.com/x/y/pull/17"},
    ])
    result = parse_pr_list(raw)
    assert result["feat/new"]["pr_status"] == "open"
