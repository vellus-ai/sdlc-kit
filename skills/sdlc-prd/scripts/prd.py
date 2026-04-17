#!/usr/bin/env python3
"""Generate a PRD document in 01-planning/."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initiative-name", required=True)
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

    slug = _slugify(args.initiative_name)
    today = date.today().isoformat()
    dest = vault / "01-planning" / f"PRD-{slug}.md"

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "file": str(dest),
            "exists": dest.exists()
        }))
        return

    if dest.exists():
        print(json.dumps({"status": "error", "message": f"PRD already exists: {dest}"}))
        sys.exit(1)

    dest.parent.mkdir(parents=True, exist_ok=True)
    content = f"""---
title: "PRD — {args.initiative_name}"
type: prd
status: draft
phase: "01"
created: {today}
updated: {today}
---

# PRD: {args.initiative_name}

## Visão

_Uma frase descrevendo o que este produto/feature faz e para quem._

## Problema

_Qual dor estamos resolvendo? Qual o impacto atual de não resolvê-la?_

## Personas

### Persona 1: [Nome]
- **Perfil:** ...
- **Dor principal:** ...
- **Objetivo:** ...

## Requisitos

### Funcionais
- [ ] RF-01: ...
- [ ] RF-02: ...

### Não-Funcionais
- [ ] RNF-01: ...

## Métricas de Sucesso

| Métrica | Baseline | Meta | Prazo |
|---------|----------|------|-------|
| ... | ... | ... | ... |

## Fora de Escopo

- ...

## Referências

- [[_INDEX]] — Índice do vault
- [[context-map]] — Mapa de contextos (se disponível)
"""
    dest.write_text(content, encoding="utf-8")
    print(json.dumps({"status": "ok", "file": str(dest)}))


if __name__ == "__main__":
    main()
