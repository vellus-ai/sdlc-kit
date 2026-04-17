#!/usr/bin/env python3
"""Generate SDD spec trio scaffold for a feature."""
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
    parser.add_argument("--feature-name", required=True)
    parser.add_argument("--epic", default="")
    parser.add_argument("--milestone", default="")
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

    slug = _slugify(args.feature_name)
    spec_dir = vault / "03-development" / slug
    today = date.today().isoformat()

    files = {
        "requirements.md": _requirements_template(args.feature_name, args.epic, args.milestone, today, slug),
        "design.md": _design_template(args.feature_name, args.epic, today, slug),
        "tasks.md": _tasks_template(args.feature_name, args.epic, today, slug),
    }

    if args.dry_run:
        print(json.dumps({
            "status": "dry-run",
            "slug": slug,
            "spec_dir": str(spec_dir),
            "files": list(files.keys())
        }))
        return

    spec_dir.mkdir(parents=True, exist_ok=True)
    created = []
    skipped = []
    for filename, content in files.items():
        dest = spec_dir / filename
        if dest.exists():
            skipped.append(filename)
        else:
            dest.write_text(content, encoding="utf-8")
            created.append(filename)

    print(json.dumps({
        "status": "ok",
        "slug": slug,
        "spec_dir": str(spec_dir),
        "files_created": created,
        "files_skipped": skipped
    }))


def _requirements_template(name: str, epic: str, milestone: str, today: str, slug: str) -> str:
    return f"""---
title: "Requirements — {name}"
type: requirements
status: draft
phase: "03"
epic: "{epic}"
milestone: "{milestone}"
created: {today}
updated: {today}
---

# Requirements: {name}

> Notação EARS — WHEN [condição/evento], the system SHALL [ação esperada]

## Contexto

_Descreva o contexto e motivação desta feature._

## User Stories

| ID | Como... | Quero... | Para... |
|----|---------|---------|---------|
| US-01 | usuário | ... | ... |

## Requisitos Funcionais

### RF-01: [Nome]

WHEN [condição], the system SHALL [ação].

**Critérios de Aceite:**
- [ ] ...

## Requisitos Não-Funcionais

- **Performance:** WHEN [carga], the system SHALL respond within [X]ms.
- **Segurança:** The system SHALL [restrição].

## Fora de Escopo

- ...

## Referências

- [[design]] — Design técnico desta feature
- [[tasks]] — Tasks de implementação
- [[_INDEX]] — Índice do vault
"""


def _design_template(name: str, epic: str, today: str, slug: str) -> str:
    return f"""---
title: "Design — {name}"
type: design
status: draft
phase: "03"
epic: "{epic}"
created: {today}
updated: {today}
---

# Design: {name}

## Visão Geral

_Descreva a abordagem técnica em 2-3 parágrafos._

## Sequência de Fluxo

```mermaid
sequenceDiagram
    actor User
    participant System
    User->>System: [ação do usuário]
    System-->>User: [resposta]
```

## Componentes Afetados

| Componente | Mudança | Notas |
|-----------|---------|-------|
| ... | ... | ... |

## Contratos de Interface

### Entrada

```
// Descrever payload/parâmetros de entrada
```

### Saída

```
// Descrever payload/resposta esperada
```

## Tratamento de Erros

| Cenário | Comportamento |
|---------|--------------|
| ... | ... |

## Decisões de Design

- Alternativa considerada: ...
- Motivo da escolha: ...

## Referências

- [[requirements]] — Requisitos desta feature
- [[tasks]] — Tasks de implementação
- [[_INDEX]]
"""


def _tasks_template(name: str, epic: str, today: str, slug: str) -> str:
    return f"""---
title: "Tasks — {name}"
type: tasks
status: draft
phase: "03"
epic: "{epic}"
created: {today}
updated: {today}
---

# Tasks: {name}

> Baseado em [[requirements]] e [[design]].

## Implementação

- [ ] **T-01:** Escrever testes para [componente principal]
- [ ] **T-02:** Implementar [componente principal]
- [ ] **T-03:** Integrar com [sistema adjacente]
- [ ] **T-04:** Revisar com `/sdlc-kit:review`

## Testes

- [ ] **T-05:** Testes unitários (cobertura ≥ 90%)
- [ ] **T-06:** Testes de integração

## Documentação

- [ ] **T-07:** Atualizar [[_INDEX]] via `/sdlc-kit:sync`

## Referências

- [[requirements]] — Requisitos desta feature
- [[design]] — Design técnico
"""


if __name__ == "__main__":
    main()
