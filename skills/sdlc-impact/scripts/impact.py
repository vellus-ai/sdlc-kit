#!/usr/bin/env python3
"""Analyze impact of changing a concept across the vault."""
import argparse
import json
import sys
from pathlib import Path


def _search_vault(vault: Path, term: str) -> list[dict]:
    """Search all .md files for term (case-insensitive), excluding .sdlc-kit/."""
    term_lower = term.lower()
    matches = []

    for md_file in sorted(vault.rglob("*.md")):
        # Exclude .sdlc-kit/ internal files
        try:
            rel = md_file.relative_to(vault)
        except ValueError:
            continue
        if rel.parts[0] == ".sdlc-kit":
            continue

        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = text.splitlines()
        count = 0
        snippet = ""
        for line in lines:
            if term_lower in line.lower():
                count += 1
                if not snippet:
                    snippet = line.strip()[:100]

        if count > 0:
            matches.append({
                "file": str(rel).replace("\\", "/"),
                "count": count,
                "snippet": snippet,
            })

    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description="Impact analysis: find all references to a term")
    parser.add_argument("--term", required=True)
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

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "term": args.term,
            "vault": str(vault),
        }))
        return

    matches = _search_vault(vault, args.term)

    print(json.dumps({
        "status": "ok",
        "term": args.term,
        "total_files": len(matches),
        "matches": matches,
    }))


if __name__ == "__main__":
    main()
