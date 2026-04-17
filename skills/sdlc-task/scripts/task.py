#!/usr/bin/env python3
"""Manage TASKS.md."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["add", "list", "update-status"], default="list")
    parser.add_argument("--title", default="")
    parser.add_argument("--epic", default="")
    parser.add_argument("--phase", default="03")
    parser.add_argument("--branch", default="")
    parser.add_argument("--status", choices=["open", "in-progress", "done"], default="open")
    parser.add_argument("--task-id", default="", help="Task line number (1-based) for update-status")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root
    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    tasks_file = vault / "03-development" / "TASKS.md"
    today = date.today().isoformat()

    if args.action == "list":
        if not tasks_file.exists():
            print(json.dumps({"status": "ok", "tasks": []}))
            return
        tasks = []
        for i, line in enumerate(tasks_file.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("- ["):
                done = line.startswith("- [x]")
                tasks.append({"line": i, "done": done, "text": line[6:].strip()})
        print(json.dumps({"status": "ok", "tasks": tasks}))
        return

    if args.action == "add":
        checkbox = "- [ ]"
        epic_tag = f"[{args.epic}] " if args.epic else ""
        branch_tag = f" @{args.branch}" if args.branch else ""
        entry = f"{checkbox} {epic_tag}{args.title} #{args.phase}{branch_tag}\n"

        if args.dry_run:
            print(json.dumps({"status": "dry-run", "entry": entry.strip()}))
            return

        if not tasks_file.exists():
            tasks_file.parent.mkdir(parents=True, exist_ok=True)
            tasks_file.write_text(
                f"---\ntitle: \"Tasks\"\ntype: tasks\nstatus: active\nphase: \"03\"\ncreated: {today}\nupdated: {today}\n---\n\n# Tasks\n\n",
                encoding="utf-8"
            )

        with open(tasks_file, "a", encoding="utf-8") as f:
            f.write(entry)

        print(json.dumps({"status": "ok", "entry": entry.strip()}))
        return

    if args.action == "update-status":
        if not tasks_file.exists():
            print(json.dumps({"status": "error", "message": "TASKS.md not found"}))
            sys.exit(1)
        if not args.task_id:
            print(json.dumps({"status": "error", "message": "--task-id required for update-status"}))
            sys.exit(1)

        lines = tasks_file.read_text(encoding="utf-8").splitlines(keepends=True)
        try:
            line_idx = int(args.task_id) - 1
        except ValueError:
            print(json.dumps({"status": "error", "message": f"invalid task-id: {args.task_id}"}))
            sys.exit(1)

        if line_idx < 0 or line_idx >= len(lines):
            print(json.dumps({"status": "error", "message": f"line {args.task_id} out of range"}))
            sys.exit(1)

        original = lines[line_idx]
        if args.status == "done":
            updated = original.replace("- [ ]", "- [x]", 1)
        else:
            updated = original.replace("- [x]", "- [ ]", 1)

        if args.dry_run:
            print(json.dumps({"status": "dry-run", "line": args.task_id, "original": original.rstrip(), "updated": updated.rstrip()}))
            return

        lines[line_idx] = updated
        tasks_file.write_text("".join(lines), encoding="utf-8")
        print(json.dumps({"status": "ok", "line": args.task_id, "new_status": args.status}))
        return

    print(json.dumps({"status": "error", "message": f"unknown action: {args.action}"}))
    sys.exit(1)


if __name__ == "__main__":
    main()
