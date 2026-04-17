---
name: sdlc-worktree
description: Esta skill deve ser usada para gerenciar o ciclo completo de git worktrees (create, list, close, sync), ou quando o usuário invoca /sdlc-kit:worktree. Cria branches isoladas para features, rastreia status de PR via gh CLI, sugere retrospectiva ao fechar. Registra tudo em SQLite.
---

# sdlc-kit:worktree

Manages git worktrees for feature/fix branches, keeping them in sync with the SDLC Kit SQLite database.

## When to invoke
- When starting work on a new feature or fix branch (create)
- To see all active worktrees (list)
- When closing/completing a branch (close)
- To sync worktree and PR metadata into the database (sync)

## Actions

### `create`
Creates a new git worktree for a branch under `<git_root>/.worktrees/<branch-slug>`.
- `--branch` is required (e.g. `feat/login-google`)
- Optionally pass `--task-id` to associate the worktree with a task

### `list`
Lists all active worktrees for `feat/*` and `fix/*` branches via `git worktree list --porcelain`.

### `close`
Removes a worktree for the given `--branch`. Will NOT force-remove if there are uncommitted changes.

### `sync`
Syncs worktree and PR status into the `worktrees` SQLite table using `core.git.sync_worktrees`.

## Guardrails
- Never use `shell=True` in subprocess calls
- Never force-close a worktree with uncommitted changes
- Worktree paths always live at `<git_root>/.worktrees/<branch-slug>`
- Branch names follow `feat/<slug>` or `fix/<slug>` convention
- Always emit JSON on stdout; non-zero exit codes for errors
