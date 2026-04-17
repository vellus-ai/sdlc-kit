---
name: sdlc-epic
description: Esta skill deve ser usada para criar ou listar épicos em EPICS.md (append-only), ou quando o usuário invoca /sdlc-kit:epic. Épicos agrupam stories relacionadas e podem ser vinculados a milestones. Rastreados em SQLite para rastreabilidade.
---

# sdlc-kit:epic

Manages epics in `03-development/EPICS.md`.

## When to invoke
- When starting a new epic
- When linking a spec to an existing epic
- When checking epic progress

## Flow
1. Ask: epic name and description
2. Ask: target milestone
3. Generate epic entry in `03-development/EPICS.md`
4. Run `/sdlc-kit:sync`

## Guardrails
- EPICS.md is append-only — never delete existing epics
- Progress is calculated from linked tasks (don't edit manually)
