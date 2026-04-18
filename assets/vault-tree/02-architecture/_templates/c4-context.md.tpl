---
type: c4-context
title: "C4 Context — {{PROJECT_NAME}}"
slug: "context"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-c4
owner: "{{OWNER}}"
tags: [architecture, c4, context]
level: 1
---

# C4 Context — {{PROJECT_NAME}}

> _(C4 Level 1 — the system viewed from outside: who uses it, which external systems it talks to.)_

## Purpose

Explain in 1 paragraph what the system does from the user and ecosystem perspective. No internal details.

## Actors

- **<Actor 1>** — <role, motivation>
- **<Actor 2>** — <role, motivation>

## External systems

- **<External System 1>** — <what it provides or consumes>
- **<External System 2>** — <what it provides or consumes>

## Diagram

```mermaid
C4Context
    title Context of {{PROJECT_NAME}}

    Person(user, "User", "Primary user description")
    System(system, "{{PROJECT_NAME}}", "System description")
    System_Ext(extA, "External System A", "Description")
    System_Ext(extB, "External System B", "Description")

    Rel(user, system, "Uses", "HTTPS")
    Rel(system, extA, "Consumes", "REST")
    Rel(system, extB, "Publishes events", "AMQP")
```

## High-level flows

- **Flow 1:** <description of main flow between actor and system>.
- **Flow 2:** <description of secondary flow>.

## Constraints

- <technical or business constraint that affects the context>

## References

- [[container]] — C4 level 2 (containers)
- [[tech]] — technical principles
- [[_INDEX]] — global index
