#!/usr/bin/env python3
# hooks/post-vault-write.py
"""
PostToolUse hook for Claude Code.
Fires on Write / Edit / NotebookEdit.
Detects if the file is inside an SDLC vault, updates SQLite, emits sync signal.
Rate-limit: at most 1 additionalContext signal per 5 seconds per vault.
"""
import json
import sys
import time
from pathlib import Path

_RATE_LIMIT_SECS = 5
_TS_FILE = ".sdlc-kit/.last-hook-signal"
_LOG_FILE = ".sdlc-kit/hook-errors.log"

def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        return

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "NotebookEdit"):
        return

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path", "")
    if not file_path:
        return

    touched = Path(file_path)
    vault_root = _find_vault_root(touched.parent)
    if not vault_root:
        return

    try:
        _update_db(vault_root, touched)
    except Exception as e:
        _log_error(vault_root, str(e))

    if _should_signal(vault_root):
        _mark_signal(vault_root)
        output = {
            "additionalContext": (
                "A vault file was modified. "
                "Please run /sdlc-kit:sync to validate frontmatter and update _INDEX.md."
            )
        }
        print(json.dumps(output))

def _find_vault_root(start: Path) -> Path | None:
    current = start.resolve()
    while True:
        if (current / ".sdlc-kit" / "marker.json").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent

def _update_db(vault_root: Path, touched: Path) -> None:
    db_path = vault_root / ".sdlc-kit" / "db.sqlite"
    if not db_path.exists():
        return
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.db import connect
    from core.scanner import scan
    conn = connect(db_path)
    scan(vault_root, conn)

def _should_signal(vault_root: Path) -> bool:
    ts_file = vault_root / _TS_FILE
    if not ts_file.exists():
        return True
    try:
        last = float(ts_file.read_text())
        return (time.time() - last) >= _RATE_LIMIT_SECS
    except Exception:
        return True

def _mark_signal(vault_root: Path) -> None:
    ts_file = vault_root / _TS_FILE
    ts_file.write_text(str(time.time()))

def _log_error(vault_root: Path, msg: str) -> None:
    log = vault_root / _LOG_FILE
    with open(log, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

if __name__ == "__main__":
    main()
