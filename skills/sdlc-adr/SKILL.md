---
name: sdlc-kit:adr
description: Create an Architecture Decision Record with auto-numbering
---

# sdlc-kit:adr

Creates a numbered ADR in `02-architecture/ADR/`.

## When to invoke

When making any significant architectural decision: choice of database, framework, pattern, protocol, deployment strategy, etc.

## Flow

1. Ask: decision title (brief, e.g. "Use PostgreSQL for primary storage")
2. Ask: context (what forced this decision?)
3. Ask: decision (what was chosen?)
4. Ask: main consequences (positive and negative)
5. Ask: alternatives considered (at least 1)
6. Generate `02-architecture/ADR/ADR-NNN-<slug>.md` (auto-number)
7. Run `/sdlc-kit:sync`

## Guardrails

- Auto-number: read existing ADRs, next = max_number + 1
- Status always starts as "Proposed" — user promotes to Accepted
- Never delete or renumber existing ADRs
