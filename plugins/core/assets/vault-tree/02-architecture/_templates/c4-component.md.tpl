---
type: c4-component
title: "C4 Component — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-c4
owner: "{{OWNER}}"
tags: [architecture, c4, component]
level: 3
container: ""
---

# C4 Component — {{TITLE}}

> _(C4 Level 3 — zoom into a specific container: which components make it up.)_

## Target container

This view details the container **<container-name>**.

## Components

| Component | Responsibility | Technology |
|---|---|---|
| <Controller> | <receives HTTP, validates, delegates> | <ex: chi handlers> |
| <Service> | <orchestrates use cases> | |
| <Repository> | <persistence> | <ex: pgx> |
| <Adapter> | <external integration> | |

## Diagram

```mermaid
C4Component
    title Components of container <name>

    Container_Boundary(c, "<container-name>") {
        Component(ctrl, "Controller", "HTTP handlers", "Receives requests")
        Component(svc, "Service", "Use cases", "Orchestrates rules")
        Component(repo, "Repository", "pgx", "Data access")
        Component(adp, "Adapter", "External SDK", "Integrates with X")
    }
    ContainerDb(db, "Database", "PostgreSQL")
    System_Ext(extA, "External System A")

    Rel(ctrl, svc, "Calls")
    Rel(svc, repo, "Uses")
    Rel(svc, adp, "Uses")
    Rel(repo, db, "Reads/writes", "SQL")
    Rel(adp, extA, "Consumes", "REST")
```

## Main flows

- **Flow A:** <Controller → Service → Repository → Database>.
- **Flow B:** <Controller → Service → Adapter → External System>.

## Extension points

- <where new components plug in without breaking invariants>

## References

- [[container]] — C4 level 2 (containers)
- [[_INDEX]] — global index
