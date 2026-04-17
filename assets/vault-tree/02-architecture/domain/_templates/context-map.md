---
title: "Context Map — {{PROJECT_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# Context Map: {{PROJECT_NAME}}

> Mapa de Bounded Contexts e suas relações segundo Domain-Driven Design.

## Bounded Contexts

| Context | Responsabilidade | Time/Owner |
|---------|-----------------|------------|
| [Context A] | ... | ... |
| [Context B] | ... | ... |

## Relações entre Contexts

```
[Context A] --[Upstream/Downstream]--> [Context B]
[Context B] --[Partnership]----------> [Context C]
[Context C] --[Shared Kernel]--------> [Context D]
```

### [Context A] → [Context B]

- **Tipo de relação:** Customer/Supplier | Conformist | ACL | OHS | Published Language
- **Descrição:** ...
- **Contrato:** [[contracts]]

## Linguagem Ubíqua por Context

Ver [[ubiquitous-language]] para glossário completo.

## Eventos de Integração

| Evento | Produtor | Consumidor | Canal |
|--------|----------|------------|-------|
| ... | [Context A] | [Context B] | ... |

## Referências

- [[ubiquitous-language]] — Glossário
- [[aggregates]] — Agregados por context
- [[domain-events]] — Eventos de domínio
- [[_INDEX]]
