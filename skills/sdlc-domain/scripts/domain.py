#!/usr/bin/env python3
"""DDD domain documentation management for bounded contexts."""
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


def _load_template(vault: Path, template_name: str) -> str | None:
    """Try to load a template from assets/vault-tree/04-domain/_templates/."""
    template_path = vault / "assets" / "vault-tree" / "04-domain" / "_templates" / template_name
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return None


def _context_map_content(context_name: str, slug: str, today: str) -> str:
    return f"""---
title: "Context Map: {context_name}"
type: context-map
status: draft
phase: "04"
created: {today}
updated: {today}
---

# Context Map: {context_name}

## Visão Geral

_Descreva o propósito deste bounded context._

## Relações com Outros Contextos

| Contexto | Tipo de Relação | Notas |
|----------|----------------|-------|
| _Exemplo_ | Upstream/Downstream | - |

## Políticas de Anti-Corrupção

_Liste as traduções e mapeamentos necessários para isolar este contexto._

## Equipe Responsável

_Quem é dono deste bounded context?_
"""


def _ubiquitous_language_content(context_name: str, slug: str, today: str) -> str:
    return f"""---
title: "Ubiquitous Language: {context_name}"
type: ubiquitous-language
status: draft
phase: "04"
created: {today}
updated: {today}
---

# Linguagem Ubíqua: {context_name}

> Esta linguagem é compartilhada entre desenvolvedores e especialistas do domínio.
> Todos os termos devem ser usados consistentemente em código, documentação e conversas.

## Glossário

| Termo | Definição | Sinônimos Proibidos |
|-------|-----------|---------------------|
| _Exemplo_ | _Defina o conceito aqui_ | _termos a evitar_ |

## Regras de Negócio

_Liste invariantes e regras do domínio em linguagem natural._

## Referências

_Links para documentação de negócio, diagramas ou especificações externas._
"""


def _domain_events_content(context_name: str) -> str:
    return f"""---
title: "Domain Events: {context_name}"
type: domain-events
status: draft
phase: "04"
---

# Domain Events: {context_name}

_Eventos de domínio representam fatos que ocorreram no passado e são relevantes para o negócio._

"""


def action_create_context(args, vault: Path) -> int:
    if not args.context_name:
        print(json.dumps({"status": "error", "message": "--context-name is required for create-context"}))
        return 1

    slug = _slugify(args.context_name)
    today = date.today().isoformat()
    context_dir = vault / "04-domain" / slug

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "context_name": args.context_name,
            "slug": slug,
            "files": [
                str(context_dir / "context-map.md"),
                str(context_dir / "ubiquitous-language.md"),
            ],
        }))
        return 0

    context_dir.mkdir(parents=True, exist_ok=True)
    created = []

    context_map_path = context_dir / "context-map.md"
    if not context_map_path.exists():
        content = _load_template(vault, "context-map.md") or _context_map_content(args.context_name, slug, today)
        context_map_path.write_text(content, encoding="utf-8")
        created.append(str(context_map_path))

    ubiq_path = context_dir / "ubiquitous-language.md"
    if not ubiq_path.exists():
        content = _load_template(vault, "ubiquitous-language.md") or _ubiquitous_language_content(args.context_name, slug, today)
        ubiq_path.write_text(content, encoding="utf-8")
        created.append(str(ubiq_path))

    print(json.dumps({
        "status": "ok",
        "context_name": args.context_name,
        "slug": slug,
        "created": created,
    }))
    return 0


def action_add_event(args, vault: Path) -> int:
    if not args.context_name:
        print(json.dumps({"status": "error", "message": "--context-name is required for add-event"}))
        return 1
    if not args.event_name:
        print(json.dumps({"status": "error", "message": "--event-name is required for add-event"}))
        return 1

    slug = _slugify(args.context_name)
    today = date.today().isoformat()
    context_dir = vault / "04-domain" / slug
    events_path = context_dir / "domain-events.md"

    event_entry = f"\n## {args.event_name}\n\n**Trigger:** \n**Payload:** \n**Created:** {today}\n"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "context_name": args.context_name,
            "event_name": args.event_name,
            "file": str(events_path),
            "entry": event_entry,
        }))
        return 0

    context_dir.mkdir(parents=True, exist_ok=True)
    if not events_path.exists():
        events_path.write_text(_domain_events_content(args.context_name), encoding="utf-8")

    with events_path.open("a", encoding="utf-8") as f:
        f.write(event_entry)

    print(json.dumps({
        "status": "ok",
        "context_name": args.context_name,
        "event_name": args.event_name,
        "file": str(events_path),
    }))
    return 0


def action_list_contexts(args, vault: Path) -> int:
    domain_dir = vault / "04-domain"
    if not domain_dir.exists():
        print(json.dumps({"status": "ok", "contexts": []}))
        return 0

    contexts = [
        d.name
        for d in sorted(domain_dir.iterdir())
        if d.is_dir() and d.name != "_templates"
    ]

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "contexts": contexts}))
        return 0

    print(json.dumps({"status": "ok", "contexts": contexts}))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="DDD domain documentation management")
    parser.add_argument("--action", required=True, choices=["create-context", "list-contexts", "add-event"])
    parser.add_argument("--context-name")
    parser.add_argument("--event-name")
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
        "create-context": action_create_context,
        "add-event": action_add_event,
        "list-contexts": action_list_contexts,
    }
    exit_code = actions[args.action](args, vault)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
