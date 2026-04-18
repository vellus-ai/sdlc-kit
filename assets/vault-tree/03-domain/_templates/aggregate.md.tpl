---
type: domain-aggregate
title: "Aggregate — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 03
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-domain
owner: "{{OWNER}}"
tags: [domain, ddd, aggregate]
context: ""
root: ""
---

# Aggregate — {{TITLE}}

> _(DDD Aggregate — unit of transactional consistency with root, child entities and invariants.)_

## Context

This aggregate lives in the **<Context>** bounded context.

## Root (Aggregate Root)

- **Name:** `<RootEntity>`
- **Identity:** <ID type, ex: UUID v7>
- **Responsibility:** <in 1 line>

## Child entities

| Entity | Identity (local) | Responsibility |
|---|---|---|
| `<Entity1>` | <ex: sequence within aggregate> | <what it represents> |
| `<Entity2>` | | |

## Value Objects

- `<VO1>` — <description, fields, value-equality rules>.
- `<VO2>` — <description>.

## Invariants

Rules that **always** must be true after any operation. Violation = bug.

- **INV-01:** <ex: "sum of items never exceeds order limit">.
- **INV-02:** <ex: "status cannot go back from `finalized` to `in_progress`">.
- **INV-03:** <ex: "cannot have two items with the same SKU">.

## Commands (operations)

Commands are the only entry points that modify the aggregate.

### `<CommandA>(params) → Event(s)`

- **Preconditions:** <expected state, authorization>.
- **Effect:** <state change>.
- **Emitted events:** [[<event-slug>]]
- **Invariants verified:** INV-01, INV-03.

### `<CommandB>(params)`

- **Preconditions:** …
- **Effect:** …
- **Emitted events:** …

## Emitted events

- [[<event-slug-1>]] — <when>
- [[<event-slug-2>]] — <when>

## Concurrency policy

- **Optimistic versioning** with `version` field (optimistic locking).
- **Conflict:** return `CONFLICT` to client with current version.

## Consistency

- **Within aggregate:** strong consistency (transactional).
- **Between aggregates:** eventual consistency via domain events.

## Example lifecycle

```
New  --CommandA-->  Active  --CommandB-->  Finalized
                     │
                     └--CommandC--> Cancelled
```

## References

- [[context-map]] — contexts map
- [[ubiquitous-language]] — glossary
- [[_INDEX]] — global index
