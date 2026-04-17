#!/usr/bin/env python3
"""Update a specific section in .sdlc/CLAUDE.md."""
import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root")
    parser.add_argument("--section", required=True, help="Section heading to update (e.g. 'Stack Tecnológica')")
    parser.add_argument("--content", required=True, help="Content to append/set in that section")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from core.paths import find_vault_root
    vault = Path(args.vault_root) if args.vault_root else find_vault_root()
    if not vault:
        print(json.dumps({"status": "error", "message": "vault not found"}))
        sys.exit(2)

    claude_md = vault / "CLAUDE.md"
    if not claude_md.exists():
        print(json.dumps({"status": "error", "message": "CLAUDE.md not found in vault"}))
        sys.exit(1)

    content = claude_md.read_text(encoding="utf-8")
    section_header = f"## {args.section}"

    if section_header in content:
        # Append to existing section (before next ## heading)
        lines = content.split("\n")
        new_lines = []
        in_section = False
        appended = False
        for line in lines:
            new_lines.append(line)
            if line.startswith(section_header):
                in_section = True
            elif in_section and line.startswith("## ") and not appended:
                new_lines.insert(-1, "")
                new_lines.insert(-1, args.content)
                appended = True
                in_section = False
        if in_section and not appended:
            new_lines.extend(["", args.content])
        new_content = "\n".join(new_lines)
        action = "updated"
    else:
        # Add new section at end
        new_content = content.rstrip() + f"\n\n## {args.section}\n\n{args.content}\n"
        action = "created"

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "action": action, "section": args.section}))
        return

    claude_md.write_text(new_content, encoding="utf-8")
    print(json.dumps({"status": "ok", "action": action, "section": args.section}))


if __name__ == "__main__":
    main()
