---
type: domain-contract
title: "Contract — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 03
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-domain
owner: "{{OWNER}}"
tags: [domain, ddd, contract, acl]
upstream_context: ""
downstream_context: ""
pattern: "ACL"
---

# Contract — {{TITLE}}

> _(Contract between bounded contexts — defines mapping, direction and translation rules.)_

## Involved contexts

- **Upstream:** <Context A> — owner of canonical model.
- **Downstream:** <Context B> — consumes and translates.
- **Pattern:** <ACL / OHS / PL / C/S / Conformist / Shared Kernel>.

## Direction

- [ ] A → B (only)
- [ ] B → A (only)
- [ ] Bidirectional

## Why it exists

Justify the pattern choice. Ex: _"ACL because A's model is legacy and has concepts that don't make sense in B."_

## Concept mapping

Explicit translations between models.

| Upstream concept | Downstream concept | Translation rule |
|---|---|---|
| `LegacyAccount` | `Account` | copy fields X, Y; ignore Z; hash ID |
| `StatusCode` (int) | `StatusEnum` (string) | map: 1→ACTIVE, 2→INACTIVE, 9→BLOCKED |
| `Currency` (free text) | `Currency` (ISO 4217) | validate against allowlist; reject unknown |

## Translation rules

- Unknown values: <strategy — reject / map to `unknown` / fallback>.
- Missing fields: <default / error>.
- Numeric types: <rounding, units>.
- Dates and timezones: <UTC / local>.

## Technical contract

- **Transport:** <REST / gRPC / events>.
- **Authentication:** <how upstream authenticates downstream>.
- **SLA:** <availability, latency>.
- **Published schema:** [[<api-slug>]]

## Versioning

- **Current version:** 1.0
- **Breaking change policy:** <deprecation window, coexistence>.

## Risks and mitigations

- **Risk:** upstream changes model → downstream breaks.
  - **Mitigation:** consumer-driven contract tests in CI.
- **Risk:** incomplete translation silently.
  - **Mitigation:** log + alert when fallback is used.

## References

- [[context-map]] — contexts map
- [[_INDEX]] — global index
