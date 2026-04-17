---
name: sdlc-prd
description: Esta skill deve ser usada para criar um Product Requirements Document (PRD) em 01-planning/, ou quando o usuário invoca /sdlc-kit:prd. Gera documento estruturado com objetivos, escopo, critérios de sucesso e stakeholders. Use para iniciativas macro antes de decompor em features individuais.
---

# sdlc-kit:prd

Creates a full PRD document in `01-planning/`.

## When to invoke

At the start of a new initiative, before creating specs for individual features.

## Flow

1. Ask: initiative name
2. Ask: problem being solved (1-2 sentences)
3. Ask: target personas (brief descriptions)
4. Ask: 3-5 key requirements (functional)
5. Ask: success metrics
6. Generate `01-planning/PRD-<slug>.md`
7. Run `/sdlc-kit:sync`

## Guardrails

- One PRD per initiative — check if one already exists
- PRD is the source of truth for requirements; specs refine it
- Always include "Fora de Escopo" section
