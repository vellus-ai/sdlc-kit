---
type: branch
title: "Branch — {{TITLE}}"
slug: "{{SLUG}}"
status: open
phase: 05
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-worktree
owner: "{{OWNER}}"
tags: [development, branch]
branch_type: "feat"
base: "main"
pr: ""
ci_status: "unknown"
---

# Branch — {{TITLE}}

> _(Branch ↔ task ↔ PR correlation with CI status.)_

## Metadata

- **Name:** `<feat/slug>` / `<fix/slug>` / `<chore/slug>`
- **Type:** `feat` / `fix` / `chore` / `refactor` / `docs` / `test`
- **Base:** `main`
- **PR:** [<number>](<url>)
- **CI Status:** 🟢 passing / 🟡 running / 🔴 failed / ⚪ pending

## Linked task

- **Feature:** [[<feature>-design]]
- **Tasks covered:**
  - [[<feature>-tasks#TASK-NNN]]
  - [[<feature>-tasks#TASK-MMM]]

## Main commits

| SHA | Message | Date |
|---|---|---|
| `<sha>` | `feat(scope): message` | {{DATE}} |
| `<sha>` | `test(scope): message` | {{DATE}} |

## Merge checklist

- [ ] Conventional Commits respected.
- [ ] Automated tests passing.
- [ ] Coverage ≥ 85% in modified package.
- [ ] CI green (lint + test + security).
- [ ] Code review approved with checklist.
- [ ] Rebase with updated `main`.
- [ ] Squash merge applied.

## History

- `{{DATE}}` — branch created from `main@<sha>`.
- `{{DATE}}` — PR opened: #<number>.

## References

- **Worktree:** [[<worktree-slug>]]
- **PR review:** [[<pr-num>-review]] (after merge)
- [[_INDEX]] — global index
