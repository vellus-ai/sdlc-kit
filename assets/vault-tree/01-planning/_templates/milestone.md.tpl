---
type: milestone
title: "{{TITLE}}"
slug: "{{SLUG}}"
status: planned
phase: 01
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-milestone
owner: "{{OWNER}}"
tags: [planning, milestone]
target_date: ""
---

# {{TITLE}}

> _(Milestone — delivery marker with target date and aggregated epic status.)_

## Target date

**{{TITLE}}** is scheduled for `<YYYY-MM-DD>`.

## Status

The milestone status is tracked in frontmatter (`status:` field) and moves through:

- `planned` — scoped, not yet started.
- `on-track` 🟢 — active and on schedule.
- `at-risk` 🟡 — active, schedule is threatened; needs attention.
- `slipped` 🔴 — target date missed or unreachable without action.
- `done` — delivered.

Flip status via `/sdlc-kit:milestone {start|at-risk|slip|done|cancel} <slug>`. Changes are logged by `/sdlc-kit:sync`; don't edit the frontmatter by hand.

_Change history (maintained manually when rationale matters):_
- `{{DATE}}` — initial status: planned.

## Aggregated scope

Epics that make up this milestone:

- [[<epic-slug-1>]] — <short status>
- [[<epic-slug-2>]] — <short status>
- [[<epic-slug-3>]] — <short status>

## Success criteria

The milestone is considered delivered when:

- [ ] All linked epics are in `status: done`.
- [ ] <measurable product criterion (KPI)>.
- [ ] <measurable technical criterion>.

## Active risks

| Risk | RAG | Mitigation |
|---|---|---|
| <risk 1> | 🟡 | <action> |

## External dependencies

- <dependency (another team, vendor, compliance, etc.)>

## References

- **Associated PRDs:** [[<prd-slug>]]
- [[_INDEX]] — global index
