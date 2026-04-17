---
name: sdlc-kit:epic
description: Create and manage epics with progress tracking
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
