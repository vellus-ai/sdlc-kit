#!/usr/bin/env python3
"""Show vault status summary."""
import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root, get_db_path
    from core.db import connect, run_migrations

    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)

    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    db_path = get_db_path(vault)
    if not db_path.exists():
        print(json.dumps({"status": "error", "message": "db not initialized — run sdlc-kit init-db"}))
        sys.exit(1)

    conn = connect(db_path)
    run_migrations(conn)

    notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    open_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]
    done_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    adrs_accepted = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='accepted'").fetchone()[0]
    adrs_proposed = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='proposed'").fetchone()[0]

    phases = {}
    for row in conn.execute("SELECT phase, COUNT(*) FROM notes GROUP BY phase"):
        phases[row[0] or "unknown"] = row[1]

    print(json.dumps({
        "status": "ok",
        "vault": str(vault),
        "notes_total": notes,
        "notes_by_phase": phases,
        "tasks": {"open": open_tasks, "done": done_tasks},
        "adrs": {"accepted": adrs_accepted, "proposed": adrs_proposed},
    }))


if __name__ == "__main__":
    main()
