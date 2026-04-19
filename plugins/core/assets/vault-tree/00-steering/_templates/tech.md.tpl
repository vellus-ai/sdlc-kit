---
type: steering-tech
title: "Technical Principles — {{PROJECT_NAME}}"
slug: "tech"
status: draft
phase: 00
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-steer
owner: "{{OWNER}}"
tags: [steering, tech, principles]
stack: "{{STACK}}"
---

# Technical Principles — {{PROJECT_NAME}}

> _(How we build: stack, trade-offs, non-negotiable rules.)_

## Stack

{{STACK_DETAILS}}

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Backend | <ex: Go 1.22> | | |
| Frontend | <ex: Next.js 15> | | |
| Database | | | |
| Messaging | | | |
| Infrastructure | | | |

## Technical principles

- **Principle 1** — <ex: "Local-first: decisions can be made without network">.
- **Principle 2** — <ex: "Fail fast, recover faster">.
- **Principle 3** — <ex: "Infrastructure as Code — zero manual configuration">.

## Accepted trade-offs

Explicit decisions on what we give up and why.

- **Trade-off 1:** <what was sacrificed> in favor of <what was prioritized>. _Reference:_ [[ADR-NNNN-slug]].
- **Trade-off 2:** …

## Founding ADRs

ADRs that anchor the project's structural decisions.

- [[ADR-0001-<slug>]] — <short title>
- [[ADR-0002-<slug>]] — <short title>

## Quality rules

- **Minimum test coverage:** <ex: 85%> in critical packages.
- **Lint:** <tool and mandatory rules>.
- **Security scan:** <ex: Trivy + Semgrep in CI>.
- **Code review:** <ex: 1 approval + AppSec checklist>.
- **Conventional Commits:** mandatory.

## References

- [[product]] — product vision
- [[standards]] — team standards
- [[CLAUDE]] — vault doctrine
