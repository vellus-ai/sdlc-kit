---
name: sdlc-kit:retro
description: Create retrospective documents and track action items
---

# sdlc-kit:retro

Manages sprint/cycle retrospective documents in `07-retrospectives/`.

## When to invoke
- At the end of a sprint or iteration to create a retrospective
- To list all existing retrospectives
- To add action items to an existing retrospective

## Actions

### `create`
Creates a new retrospective document at `07-retrospectives/retro-<slug>.md`.
- `--sprint` is required (e.g. `Sprint 23` or `2026-04`)
- Exits with error if the file already exists

### `list`
Lists all `retro-*.md` files in `07-retrospectives/`, returning title and status from frontmatter.

### `add-action`
Appends an action item (`- [ ] <text>`) to the `## Itens de ação` section of a retro file.
- `--action-item` is required
- `--retro-file` is required (filename, e.g. `retro-sprint-23.md`)

## Document structure

```markdown
---
title: "Retro: Sprint 23"
type: retrospective
status: draft
phase: "07"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Retro: Sprint 23

## O que foi bem

## O que pode melhorar

## Itens de ação

## Próximos passos
```

## Guardrails
- Never overwrite an existing retro; exit 1 if file exists on create
- The `## Itens de ação` section must exist before adding action items
- Always emit JSON on stdout; non-zero exit codes for errors
- `--dry-run` must produce no file-system side effects
