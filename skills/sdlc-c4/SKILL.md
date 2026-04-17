---
name: sdlc-c4
description: Esta skill deve ser usada para gerar diagramas C4 em Mermaid (C4Context, Container, Component), ou quando o usuário invoca /sdlc-kit:c4. Produz arquivos markdown com diagramas renderizáveis em 02-architecture/. Use para documentar arquitetura em 3 níveis de granularidade.
---

# sdlc-kit:c4

Creates C4 model diagrams (Context, Container, Component) using Mermaid syntax under `02-architecture/`.

## When to invoke

When documenting system architecture at any level of abstraction using the C4 model.

## Flow

1. Ask: diagram level (`context` | `container` | `component`)
2. Ask: system name
3. Generate `02-architecture/c4-<level>-<slug>.md` with a Mermaid starter template
4. Run `/sdlc-kit:sync`

## Levels

- **context**: Shows the system in context with users and external systems (`C4Context`)
- **container**: Shows high-level technical containers within the system (`C4Container`)
- **component**: Shows components within a specific container (`C4Component`)

## Guardrails

- Never overwrite an existing diagram — exit with error if file already exists
- Status always starts as "draft"; promote to "approved" after team review
- Use Mermaid C4 syntax compatible with Obsidian's Mermaid renderer
