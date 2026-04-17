#!/usr/bin/env python3
"""Manage epics in 03-development/EPICS.md."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epic-name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--milestone", default="")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true", help="List all epics")
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

    epics_file = vault / "03-development" / "EPICS.md"
    today = date.today().isoformat()

    if args.list:
        if not epics_file.exists():
            print(json.dumps({"status": "ok", "epics": []}))
            return
        content = epics_file.read_text(encoding="utf-8")
        epics = [line.strip("# ").strip() for line in content.splitlines()
                 if line.startswith("## ") and not line.startswith("## Épicos")]
        print(json.dumps({"status": "ok", "epics": epics}))
        return

    entry = f"\n## {args.epic_name}\n\n**Milestone:** {args.milestone}\n**Descrição:** {args.description}\n**Criado:** {today}\n**Progresso:** 0%\n"

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "epic_name": args.epic_name, "entry_preview": entry.strip()}))
        return

    if not epics_file.exists():
        epics_file.parent.mkdir(parents=True, exist_ok=True)
        epics_file.write_text(
            "---\ntitle: \"Épicos\"\ntype: epic\nstatus: active\nphase: \"03\"\ncreated: " + today + "\nupdated: " + today + "\n---\n\n# Épicos\n",
            encoding="utf-8"
        )

    with open(epics_file, "a", encoding="utf-8") as f:
        f.write(entry)

    print(json.dumps({"status": "ok", "epic_name": args.epic_name, "file": str(epics_file)}))


if __name__ == "__main__":
    main()
