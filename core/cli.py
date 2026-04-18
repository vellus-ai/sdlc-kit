import json
import sys


def main() -> None:
    cmds = {"init-db": _init_db, "scan": _scan, "status": _status}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print("Usage: sdlc-kit <command>")
        print("Commands:", ", ".join(cmds))
        sys.exit(1)
    cmds[sys.argv[1]]()

def _require_vault():
    from .db import connect, run_migrations
    from .paths import find_vault_root, get_db_path
    vault = find_vault_root()
    if not vault:
        print("ERROR: No vault found. Run /sdlc-kit:init first.", file=sys.stderr)
        sys.exit(2)
    db_path = get_db_path(vault)
    conn = connect(db_path)
    run_migrations(conn)
    return vault, conn

def _init_db() -> None:
    from .db import connect, run_migrations
    from .paths import find_vault_root, get_db_path
    vault = find_vault_root()
    if not vault:
        print("ERROR: No vault found.", file=sys.stderr)
        sys.exit(2)
    db_path = get_db_path(vault)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    run_migrations(conn)
    print(json.dumps({"status": "ok", "db": str(db_path)}))

def _scan() -> None:
    from .scanner import scan
    vault, conn = _require_vault()
    result = scan(vault, conn)
    print(json.dumps(result))

def _status() -> None:
    vault, conn = _require_vault()
    notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    open_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]
    done_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    adrs = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    print(json.dumps({
        "vault": str(vault),
        "notes": notes,
        "tasks": {"open": open_tasks, "done": done_tasks},
        "adrs": adrs,
    }))

if __name__ == "__main__":
    main()
