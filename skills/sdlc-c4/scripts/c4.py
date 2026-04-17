#!/usr/bin/env python3
"""Generate C4 architecture diagrams in Mermaid markdown."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


def _slugify(name: str) -> str:
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return slug


def _mermaid_context(system_name: str) -> str:
    return f"""```mermaid
C4Context
    title System Context diagram for {system_name}

    Person(user, "User", "A user of {system_name}")
    System(system, "{system_name}", "The system being described")
    System_Ext(ext1, "External System", "An external dependency")

    Rel(user, system, "Uses")
    Rel(system, ext1, "Calls")
```"""


def _mermaid_container(system_name: str) -> str:
    return f"""```mermaid
C4Container
    title Container diagram for {system_name}

    Person(user, "User", "A user of {system_name}")

    System_Boundary(sys_boundary, "{system_name}") {{
        Container(web_app, "Web Application", "TypeScript/React", "Delivers the UI")
        Container(api, "API", "Go/REST", "Handles business logic")
        ContainerDb(db, "Database", "PostgreSQL", "Stores application data")
    }}

    Rel(user, web_app, "Uses", "HTTPS")
    Rel(web_app, api, "Calls", "HTTPS/JSON")
    Rel(api, db, "Reads/Writes", "SQL")
```"""


def _mermaid_component(system_name: str) -> str:
    return f"""```mermaid
C4Component
    title Component diagram for {system_name}

    Container_Boundary(container_boundary, "{system_name} API") {{
        Component(router, "Router", "chi", "Routes HTTP requests")
        Component(handler, "Handler", "Go", "Handles request/response")
        Component(service, "Service", "Go", "Business logic")
        Component(repo, "Repository", "pgx", "Data access layer")
    }}

    Rel(router, handler, "Dispatches to")
    Rel(handler, service, "Calls")
    Rel(service, repo, "Uses")
```"""


MERMAID_BUILDERS = {
    "context": _mermaid_context,
    "container": _mermaid_container,
    "component": _mermaid_component,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate C4 architecture diagrams")
    parser.add_argument("--level", required=True, choices=["context", "container", "component"])
    parser.add_argument("--system-name", required=True)
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

    slug = _slugify(args.system_name)
    today = date.today().isoformat()
    filename = f"c4-{args.level}-{slug}.md"
    dest = vault / "02-architecture" / filename

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "level": args.level,
            "system_name": args.system_name,
            "file": str(dest),
        }))
        return

    if dest.exists():
        print(json.dumps({"status": "error", "message": f"diagram already exists: {dest}"}))
        sys.exit(1)

    mermaid_block = MERMAID_BUILDERS[args.level](args.system_name)

    content = f"""---
title: "C4 {args.level.capitalize()}: {args.system_name}"
type: c4-diagram
level: {args.level}
status: draft
phase: "02"
created: {today}
updated: {today}
---

# C4 {args.level.capitalize()} Diagram: {args.system_name}

> Generated starter template. Edit to reflect the actual architecture.

{mermaid_block}

## Notas

_Adicione contexto e decisões relevantes sobre esta visão arquitetural._
"""

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "level": args.level,
        "system_name": args.system_name,
        "file": str(dest),
    }))


if __name__ == "__main__":
    main()
