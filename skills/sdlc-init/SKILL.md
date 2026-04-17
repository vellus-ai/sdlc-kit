---
name: sdlc-kit:init
description: Scaffold a new SDLC vault inside the current Git repository
---

# sdlc-kit:init

Scaffold a complete SDLC vault at `.sdlc/` in the current project root.

## When to invoke

When the user wants to initialize SDLC Kit in a new project for the first time.
Also safe to re-run — idempotent (skips existing files).

## Flow

1. Ask 7 questions (one at a time):
   - Project name
   - Tech stack (languages, frameworks)
   - Owner/team name
   - Repository URL (optional)
   - Main bounded contexts (optional — can skip with "não sei ainda")
   - Design system needed? (y/n)
   - Use git worktrees for parallel agents? (y/n)

2. Run `python skills/sdlc-init/scripts/scaffold.py --vault-root <project-root>/.sdlc --project-name "..." --owner "..." --stack "..." [--repo-url "..."]`

3. Run `sdlc-kit init-db` (from within the .sdlc directory)

4. Append to project root CLAUDE.md:
   ```
   ## SDLC Vault
   Leia [[.sdlc/_INDEX]] antes de iniciar qualquer tarefa.
   Doutrina do vault: `.sdlc/CLAUDE.md`
   ```

5. Confirm success and show next steps:
   - "Vault criado em `.sdlc/`. Próximos passos:"
   - "1. `/sdlc-kit:prd` — criar PRD da iniciativa"
   - "2. `/sdlc-kit:domain` — modelar bounded contexts (se aplicável)"
   - "3. `/sdlc-kit:spec <feature>` — criar sua primeira spec SDD"

## Guardrails

- Never overwrite existing CLAUDE.md, _INDEX.md, or user documents
- Always run sync after scaffold
- If .sdlc/ already exists, report which files were skipped
