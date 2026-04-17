---
name: sdlc-task
description: Esta skill deve ser usada para adicionar, listar ou atualizar status de tarefas em TASKS.md, ou quando o usuário invoca /sdlc-kit:task. Suporta vinculação com épicos via [EPIC] e com branches via @branch. Estados: open, in-progress, done.
---

# sdlc-kit:task

Manages `03-development/TASKS.md`.

## Task format

```
- [ ] [EPIC] Task title #phase @branch
- [x] [EPIC] Completed task #phase @branch
```

## When to invoke
- To add a new task
- To update task status (open → in-progress → done)
- To link a task to a branch

## Guardrails
- TASKS.md is the single source of truth for task status
- Branch names follow `feat/<slug>` or `fix/<slug>` convention
- Always run sync after updates
