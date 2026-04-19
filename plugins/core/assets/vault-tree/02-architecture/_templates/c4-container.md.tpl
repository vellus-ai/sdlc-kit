---
type: c4-container
title: "C4 Container — {{PROJECT_NAME}}"
slug: "container"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-c4
owner: "{{OWNER}}"
tags: [architecture, c4, container]
level: 2
---

# C4 Container — {{PROJECT_NAME}}

> _(C4 Level 2 — zoom into the system: which applications, services and data stores exist and how they connect.)_

## Purpose

Explain the internal blocks (containers) of the system and their high-level responsibilities.

## Containers

| Container | Technology | Responsibility |
|---|---|---|
| <API Gateway> | <ex: Kong> | <routing, rate limiting> |
| <Backend Service> | <ex: Go/chi> | <business logic> |
| <Frontend Web> | <ex: Next.js> | <user UI> |
| <Database> | <ex: PostgreSQL> | <persistence> |
| <Cache> | <ex: Redis> | <session, lightweight queue> |
| <Message Broker> | <ex: Kafka> | <async events> |

## Diagram

```mermaid
C4Container
    title Containers of {{PROJECT_NAME}}

    Person(user, "User")
    System_Boundary(sys, "{{PROJECT_NAME}}") {
        Container(web, "Frontend Web", "Next.js", "User UI")
        Container(api, "Backend API", "Go/chi", "REST endpoints")
        ContainerDb(db, "Database", "PostgreSQL", "Transactional data")
        Container(cache, "Cache", "Redis", "Session and lightweight queue")
    }

    Rel(user, web, "Uses", "HTTPS")
    Rel(web, api, "Calls", "REST/JSON")
    Rel(api, db, "Reads/writes", "SQL")
    Rel(api, cache, "Reads/writes", "RESP")
```

## Communication between containers

- **web → api:** <protocol, auth, rate limiting>.
- **api → db:** <protocol, connection pool>.
- **api → cache:** <protocol, default TTL>.

## Related decisions

- [[ADR-NNNN-<slug>]] — <container 1 decision>
- [[ADR-NNNN-<slug>]] — <container 2 decision>

## References

- [[context]] — C4 level 1 (context)
- [[component]] — C4 level 3 (components)
- [[_INDEX]] — global index
