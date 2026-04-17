#!/usr/bin/env python3
"""Create a numbered ADR in 02-architecture/ADR/."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


def _slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug


def _next_adr_number(adr_dir: Path) -> int:
    if not adr_dir.exists():
        return 1
    numbers = []
    for f in adr_dir.glob("ADR-*.md"):
        m = re.match(r"ADR-(\d+)", f.name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
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

    adr_dir = vault / "02-architecture" / "ADR"
    number = _next_adr_number(adr_dir)
    slug = _slugify(args.title)
    filename = f"ADR-{number:03d}-{slug}.md"
    dest = adr_dir / filename
    today = date.today().isoformat()

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "next_number": number,
            "filename": filename,
            "file": str(dest)
        }))
        return

    adr_dir.mkdir(parents=True, exist_ok=True)
    content = f"""---
title: "ADR-{number:03d}: {args.title}"
type: adr
status: proposed
phase: "02"
created: {today}
updated: {today}
---

# ADR-{number:03d}: {args.title}

**Status:** Proposed

## Contexto

_Qual problema ou necessidade motivou esta decisão?_

## Decisão

_O que foi decidido? Seja direto e afirmativo._

## Consequências

### Positivas
- ...

### Negativas
- ...

## Alternativas Consideradas

### Alternativa 1: [Nome]
- **Motivo de rejeição:** ...

## Referências

- [[_INDEX]]
"""
    dest.write_text(content, encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "number": number,
        "filename": filename,
        "file": str(dest)
    }))


if __name__ == "__main__":
    main()
