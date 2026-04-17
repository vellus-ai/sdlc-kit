#!/usr/bin/env python3
"""Generate a document from a vault template."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

_PHASE_FOLDERS = {
    "01": "01-planning",
    "02": "02-architecture",
    "03": "03-development",
    "04": "04-testing",
    "05": "05-deployment",
    "06": "06-decisions",
    "07": "07-retrospectives",
}


def _slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--template", required=True, help="Template filename, e.g. test-plan.md")
    parser.add_argument("--phase", required=True, help="Phase number, e.g. 04")
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

    phase_folder = _PHASE_FOLDERS.get(args.phase)
    if not phase_folder:
        print(json.dumps({"status": "error", "message": f"unknown phase: {args.phase}"}))
        sys.exit(1)

    # Find the plugin root to locate assets
    plugin_root = Path(__file__).parent.parent.parent.parent
    template_path = plugin_root / "assets" / "vault-tree" / phase_folder / "_templates" / args.template
    if not template_path.exists():
        print(json.dumps({"status": "error", "message": f"template not found: {template_path}"}))
        sys.exit(1)

    slug = _slugify(args.title)
    today = date.today().isoformat()
    dest = vault / phase_folder / f"{slug}.md"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "template": str(template_path),
            "destination": str(dest),
            "exists": dest.exists()
        }))
        return

    if dest.exists():
        print(json.dumps({"status": "error", "message": f"file already exists: {dest}"}))
        sys.exit(1)

    content = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{TITLE}}": args.title,
        "{{DATE}}": today,
        "{{FEATURE_NAME}}": args.title,
        "{{INITIATIVE_NAME}}": args.title,
    }
    for k, v in replacements.items():
        content = content.replace(k, v)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print(json.dumps({"status": "ok", "file": str(dest)}))


if __name__ == "__main__":
    main()
