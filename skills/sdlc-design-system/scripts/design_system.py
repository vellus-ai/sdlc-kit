#!/usr/bin/env python3
"""Create or update design system documentation."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _tokens_initial_content(today: str) -> str:
    return f"""---
title: Design Tokens
type: design-tokens
status: draft
phase: "06"
created: {today}
updated: {today}
---

# Design Tokens

> Design tokens são os valores atômicos do design system: cores, espaçamentos, tipografia, etc.

| Nome | Categoria | Valor | Adicionado |
|------|-----------|-------|------------|
"""


def _components_initial_content(today: str) -> str:
    return f"""---
title: Components
type: design-components
status: draft
phase: "06"
created: {today}
updated: {today}
---

# Componentes

> Documentação de componentes reutilizáveis do design system.

"""


def _patterns_initial_content(today: str) -> str:
    return f"""---
title: Patterns
type: design-patterns
status: draft
phase: "06"
created: {today}
updated: {today}
---

# Padrões de Design

> Padrões de interação e composição de componentes para casos de uso recorrentes.

"""


def action_init(args, vault: Path) -> int:
    today = date.today().isoformat()
    ds_dir = vault / "06-design-system"

    files = {
        "tokens.md": _tokens_initial_content(today),
        "components.md": _components_initial_content(today),
        "patterns.md": _patterns_initial_content(today),
    }

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "directory": str(ds_dir),
            "files": list(files.keys()),
        }))
        return 0

    ds_dir.mkdir(parents=True, exist_ok=True)
    created = []
    skipped = []

    for filename, content in files.items():
        path = ds_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(filename)
        else:
            skipped.append(filename)

    print(json.dumps({
        "status": "ok",
        "created": created,
        "skipped": skipped,
    }))
    return 0


def action_add_token(args, vault: Path) -> int:
    if not args.name:
        print(json.dumps({"status": "error", "message": "--name is required for add-token"}))
        return 1
    if not args.value:
        print(json.dumps({"status": "error", "message": "--value is required for add-token"}))
        return 1
    if not args.category:
        print(json.dumps({"status": "error", "message": "--category is required for add-token"}))
        return 1

    today = date.today().isoformat()
    tokens_path = vault / "06-design-system" / "tokens.md"
    row = f"| {args.name} | {args.category} | {args.value} | {today} |\n"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "file": str(tokens_path),
            "row": row.strip(),
        }))
        return 0

    if not tokens_path.exists():
        tokens_path.parent.mkdir(parents=True, exist_ok=True)
        tokens_path.write_text(_tokens_initial_content(today), encoding="utf-8")
    else:
        existing = tokens_path.read_text(encoding="utf-8")
        if f"| {args.name} |" in existing:
            print(json.dumps({"status": "skipped", "reason": "token already exists", "name": args.name}))
            return 0

    with tokens_path.open("a", encoding="utf-8") as f:
        f.write(row)

    print(json.dumps({
        "status": "ok",
        "name": args.name,
        "category": args.category,
        "value": args.value,
        "file": str(tokens_path),
    }))
    return 0


def action_add_component(args, vault: Path) -> int:
    if not args.name:
        print(json.dumps({"status": "error", "message": "--name is required for add-component"}))
        return 1

    today = date.today().isoformat()
    components_path = vault / "06-design-system" / "components.md"
    entry = f"\n## {args.name}\n\n**Status:** draft\n**Added:** {today}\n"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "file": str(components_path),
            "entry": entry.strip(),
        }))
        return 0

    if not components_path.exists():
        components_path.parent.mkdir(parents=True, exist_ok=True)
        components_path.write_text(_components_initial_content(today), encoding="utf-8")
    else:
        existing = components_path.read_text(encoding="utf-8")
        if f"\n## {args.name}\n" in existing or existing.startswith(f"## {args.name}\n"):
            print(json.dumps({"status": "skipped", "reason": "component already exists", "name": args.name}))
            return 0

    with components_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(json.dumps({
        "status": "ok",
        "name": args.name,
        "file": str(components_path),
    }))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Design system documentation management")
    parser.add_argument("--action", required=True, choices=["init", "add-token", "add-component"])
    parser.add_argument("--name")
    parser.add_argument("--value")
    parser.add_argument("--category")
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

    actions = {
        "init": action_init,
        "add-token": action_add_token,
        "add-component": action_add_component,
    }
    exit_code = actions[args.action](args, vault)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
