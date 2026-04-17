#!/usr/bin/env python3
"""Scaffold SDLC vault directory tree from assets/vault-tree/."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

_ASSETS = Path(__file__).parent.parent.parent.parent / "assets" / "vault-tree"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", required=True)
    parser.add_argument("--project-name", default="Meu Projeto")
    parser.add_argument("--owner", default="")
    parser.add_argument("--stack", default="")
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    vault = Path(args.vault_root)
    today = date.today().isoformat()
    replacements = {
        "{{PROJECT_NAME}}": args.project_name,
        "{{OWNER}}": args.owner,
        "{{STACK}}": args.stack,
        "{{STACK_DETAILS}}": args.stack,
        "{{REPO_URL}}": args.repo_url,
        "{{DATE}}": today,
        "{{SYNC_TS}}": today,
    }

    if not _ASSETS.exists():
        print(json.dumps({"status": "error", "message": f"assets not found at {_ASSETS}"}))
        sys.exit(1)

    created = []
    skipped = []

    for src in _ASSETS.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(_ASSETS)
        # Rename .tpl files
        dest_name = rel.name.replace(".tpl", "")
        dest = vault / rel.parent / dest_name

        if args.dry_run:
            if dest.exists():
                skipped.append(str(rel))
            else:
                created.append(str(rel))
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            skipped.append(str(rel))
            continue

        content = src.read_text(encoding="utf-8")
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        dest.write_text(content, encoding="utf-8")
        created.append(str(rel))

    # Create marker
    if not args.dry_run:
        kit_dir = vault / ".sdlc-kit"
        kit_dir.mkdir(exist_ok=True)
        marker = kit_dir / "marker.json"
        if not marker.exists():
            marker.write_text(json.dumps({"version": "0.1.0", "created": today}))
            created.append(".sdlc-kit/marker.json")

    status = "dry-run" if args.dry_run else "ok"
    print(json.dumps({"status": status, "files_created": created, "files_skipped": skipped}))


if __name__ == "__main__":
    main()
