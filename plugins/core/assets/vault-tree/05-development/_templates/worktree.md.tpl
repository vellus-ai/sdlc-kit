---
type: worktree
title: "Worktree — {{TITLE}}"
slug: "{{SLUG}}"
status: active
phase: 05
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-worktree
owner: "{{OWNER}}"
tags: [development, worktree]
branch: ""
base: "main"
path: ""
pr: ""
agent_active: false
---

# Worktree — {{TITLE}}

> _(Worktree log — branch, base, local path, linked task and executing agent.)_

## Metadata

- **Branch:** `<feat/slug>`
- **Base:** `main`
- **Local path:** `<path/relative/or/absolute>`
- **PR:** [<number>](<url>) (empty while open)
- **Status:** `active` / `merged` / `abandoned`

## Active agent

- [ ] AI agent connected to this worktree.

_When checked, indicates that an agent (Claude Code, etc.) is operating in this worktree and every edit triggers the PostToolUse hook._

## Linked task

- **Feature:** [[<feature>-design]]
- **Main task:** [[<feature>-tasks#TASK-NNN]]

## History

- `{{DATE}}` — created from `main@<sha>` by {{OWNER}}.

## Reference commands

```bash
# Create worktree
git worktree add ../project-<slug> <feat/slug>

# List worktrees
git worktree list

# Remove worktree after merge
git worktree remove ../project-<slug>
```

## Closure checklist

- [ ] PR approved and merged.
- [ ] CI green on final branch.
- [ ] Local branch deleted.
- [ ] Worktree removed from filesystem.
- [ ] Status updated to `merged` or `abandoned`.

## References

- **Branch:** [[<branch-slug>]]
- [[_INDEX]] — global index
