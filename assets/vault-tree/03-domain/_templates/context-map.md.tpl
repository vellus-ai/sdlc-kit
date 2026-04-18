---
type: domain-context-map
title: "Context Map — {{PROJECT_NAME}}"
slug: "context-map"
status: draft
phase: 03
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-domain
owner: "{{OWNER}}"
tags: [domain, ddd, context-map]
---

# Context Map — {{PROJECT_NAME}}

> _(Strategic DDD — bounded contexts of the project and how they relate.)_

## Purpose

This map guides decisions about integration between contexts. Poorly designed relationships between bounded contexts are the main source of accidental coupling in DDD systems.

## Bounded Contexts

| Context | Responsibility | Owning team |
|---|---|---|
| **<Context A>** | <domain handled> | <team> |
| **<Context B>** | <domain handled> | <team> |
| **<Context C>** | <domain handled> | <team> |

## Relationships between contexts

Use DDD Context Mapping patterns:

- **Shared Kernel (SK)** — contexts share a piece of model; requires strong coordination.
- **Customer / Supplier (C/S)** — upstream serves downstream; upstream accepts downstream influence.
- **Conformist (CF)** — downstream adapts to upstream without negotiating.
- **Anticorruption Layer (ACL)** — downstream translates upstream model into its own model.
- **Open Host Service (OHS)** — upstream publishes a stable API for multiple downstreams.
- **Published Language (PL)** — documented and versioned language (ex: JSON Schema, Proto).
- **Separate Ways (SW)** — contexts don't integrate.
- **Partnership (P)** — contexts co-evolve with continuous coordination.

## Relationship table

| Upstream | Downstream | Pattern | Notes |
|---|---|---|---|
| Context A | Context B | OHS + PL | Versioned REST API |
| Context A | Context C | ACL | Context C protects its model |
| Context B | Context C | C/S | Context B depends on C |

## Diagram

```mermaid
flowchart LR
    A["Context A\n(Core)"]
    B["Context B\n(Supporting)"]
    C["Context C\n(Generic)"]

    A -- "OHS/PL" --> B
    A -- "ACL" --> C
    B -- "C/S" --> C
```

## Core vs. Supporting vs. Generic

Classify each context by **domain distillation**:

- **Core domain:** competitive differentiator — invest more.
- **Supporting:** necessary but not differentiator — standard or buy.
- **Generic:** common to any company — prefer SaaS/buy.

| Context | Classification |
|---|---|
| <Context A> | Core |
| <Context B> | Supporting |
| <Context C> | Generic |

## References

- [[ubiquitous-language]] — glossary per context
- [[_INDEX]] — global index
