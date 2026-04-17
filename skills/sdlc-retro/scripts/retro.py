#!/usr/bin/env python3
"""Create and manage sprint retrospective documents."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


def _slugify(name: str) -> str:
    slug = name.lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9-]", "", slug)


def _read_frontmatter_field(content: str, field: str) -> str:
    """Extract a scalar field value from YAML frontmatter."""
    for line in content.splitlines():
        if line.startswith(f"{field}:"):
            value = line[len(field) + 1:].strip().strip('"')
            return value
    return ""


def action_create(args) -> None:
    if not args.sprint:
        print(json.dumps({"status": "error", "message": "--sprint is required for create"}))
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

    slug = _slugify(args.sprint)
    filename = f"retro-{slug}.md"
    retro_dir = vault / "07-retrospectives"
    retro_file = retro_dir / filename
    today = date.today().isoformat()

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "file": filename, "sprint": args.sprint, "slug": slug}))
        return

    if retro_file.exists():
        print(json.dumps({"status": "error", "message": f"retro file already exists: {filename}"}))
        sys.exit(1)

    retro_dir.mkdir(parents=True, exist_ok=True)

    content = (
        f'---\ntitle: "Retro: {args.sprint}"\ntype: retrospective\nstatus: draft\n'
        f'phase: "07"\ncreated: {today}\nupdated: {today}\n---\n\n'
        f'# Retro: {args.sprint}\n\n'
        f'## O que foi bem\n\n'
        f'## O que pode melhorar\n\n'
        f'## Itens de ação\n\n'
        f'## Próximos passos\n'
    )
    retro_file.write_text(content, encoding="utf-8")
    print(json.dumps({"status": "ok", "file": filename, "sprint": args.sprint}))


def action_list(args) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root

    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)
    if not (vault / ".sdlc-kit" / "marker.json").exists():
        print(json.dumps({"status": "error", "message": f"not a valid vault: {vault}"}))
        sys.exit(2)

    retro_dir = vault / "07-retrospectives"
    if not retro_dir.exists():
        print(json.dumps({"status": "ok", "retros": []}))
        return

    retros = []
    for f in sorted(retro_dir.glob("retro-*.md")):
        content = f.read_text(encoding="utf-8")
        title = _read_frontmatter_field(content, "title")
        status = _read_frontmatter_field(content, "status")
        retros.append({"file": f.name, "title": title, "status": status})

    print(json.dumps({"status": "ok", "retros": retros}))


def action_add_action(args) -> None:
    if not args.action_item:
        print(json.dumps({"status": "error", "message": "--action-item is required for add-action"}))
        sys.exit(1)
    if not args.retro_file:
        print(json.dumps({"status": "error", "message": "--retro-file is required for add-action"}))
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

    retro_file = vault / "07-retrospectives" / args.retro_file
    if not retro_file.exists():
        print(json.dumps({"status": "error", "message": f"retro file not found: {args.retro_file}"}))
        sys.exit(1)

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "retro_file": args.retro_file,
            "action_item": args.action_item,
        }))
        return

    content = retro_file.read_text(encoding="utf-8")
    section_header = "## Itens de ação"
    if section_header not in content:
        print(json.dumps({"status": "error", "message": f"section '{section_header}' not found in {args.retro_file}"}))
        sys.exit(1)

    new_item = f"- [ ] {args.action_item}"

    # Find the section and insert after it (before next ## or end of file)
    lines = content.splitlines(keepends=True)
    insert_idx = None
    in_section = False
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            # Next section found; insert before it
            insert_idx = i
            break
    if insert_idx is None and in_section:
        # Section is last; append at end
        insert_idx = len(lines)

    if insert_idx is None:
        print(json.dumps({"status": "error", "message": f"could not locate insertion point in {args.retro_file}"}))
        sys.exit(1)

    lines.insert(insert_idx, new_item + "\n")
    retro_file.write_text("".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "retro_file": args.retro_file, "action_item": args.action_item}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["create", "list", "add-action"], default="list")
    parser.add_argument("--sprint", default="")
    parser.add_argument("--action-item", default="")
    parser.add_argument("--retro-file", default="")
    parser.add_argument("--vault-root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.action == "create":
        action_create(args)
    elif args.action == "list":
        action_list(args)
    elif args.action == "add-action":
        action_add_action(args)
    else:
        print(json.dumps({"status": "error", "message": f"unknown action: {args.action}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
