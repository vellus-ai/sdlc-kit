---
name: sdlc-kit:trace
description: Generate a traceability matrix linking requirements to design to tasks
---

# sdlc-kit:trace

Generates a traceability matrix for a spec in `03-development/<slug>/`, linking requirements (EARS notation) to design artifacts and tasks.

## When to invoke

When you need to verify that all requirements have corresponding design decisions and implementation tasks, or when preparing for a review or audit.

## Flow

1. Ask: spec slug (the directory name under `03-development/`)
2. Read `requirements.md`, `design.md`, `tasks.md` from the spec directory
3. Extract requirements: lines matching `WHEN` or `SHALL` keywords (EARS notation)
4. Extract tasks: lines starting with `- [` 
5. Generate `03-development/<slug>/traceability.md` with a Markdown table
6. Run `/sdlc-kit:sync`

## Guardrails

- Exits with error if spec directory doesn't exist
- Exits with error if `requirements.md` is missing
- Missing `design.md` or `tasks.md` produces empty columns but does not fail
- Traceability file is always regenerated (idempotent overwrite)
- Never edits `requirements.md`, `design.md`, or `tasks.md`
