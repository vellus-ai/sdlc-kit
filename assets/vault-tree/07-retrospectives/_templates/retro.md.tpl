---
type: retro
title: "Retro — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 07
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-retro
owner: "{{OWNER}}"
tags: [retrospective, retro, sprint]
sprint: ""
period_start: ""
period_end: ""
---

# Retro — {{TITLE}}

> _(Sprint retrospective — what to keep, improve, stop, and which actions we commit to.)_

## Period

- **Sprint:** `<sprint-name>`
- **From:** `<YYYY-MM-DD>`
- **To:** `<YYYY-MM-DD>`
- **Duration:** <ex: 2 weeks>

## Automatic summary

_(Pre-populated by `sprint close` hook — adjust only if something is incorrect.)_

### Tasks closed in period

- <N tasks>
- _(auto-generated list from SQLite, ex:)_
  - [[<feature>-tasks#TASK-001]] — `feat: ...`
  - [[<feature>-tasks#TASK-002]] — `fix: ...`

### Specs delivered

- [[<feature-slug>]] — `status: approved`
- [[<feature-slug>]] — `status: approved`

### ADRs created

- [[ADR-NNNN-<slug>]] — `status: accepted`

### Incidents in period

- [[<incident-slug>]] — SEV<N>, `status: resolved`, MTTR <time>

### Milestones — RAG status

- [[<milestone-slug>]] — 🟢 Green
- [[<milestone-slug>]] — 🟡 Amber

---

## ✅ Keep

What worked well and we should maintain.

- <item>
- <item>

## ⚠️ Improve

What needs adjustment without stopping it.

- <item>
- <item>

## ❌ Stop

Practices or behaviors to discontinue.

- <item>
- <item>

## 🎯 Actions

Concrete actions, with owner and deadline. Each action should become a task or ADR.

| Action | Owner | Deadline | Artifact |
|---|---|---|---|
| <description> | <name> | <date> | [[<link>]] |
| <description> | <name> | <date> | — |

## Team mood

- **Energy:** 🟢 / 🟡 / 🔴
- **Confidence in next sprint:** 🟢 / 🟡 / 🔴
- **Notes:** <free text>

## References

- **Previous retro:** [[<prev-retro-slug>]]
- [[_INDEX]] — global index
