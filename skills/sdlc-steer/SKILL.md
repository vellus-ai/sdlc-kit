---
name: sdlc-kit:steer
description: Update vault steering rules in CLAUDE.md
---

# sdlc-kit:steer

Safely merges updates into the vault's `CLAUDE.md` doctrine.

## When to invoke

When the user wants to update:
- Coding standards or conventions
- Stack technology changes
- New architectural constraints
- Team norms or processes

## Flow

1. Ask what the user wants to add/update (be specific)
2. Read current `.sdlc/CLAUDE.md`
3. Identify which section to update or if a new section is needed
4. Run `python skills/sdlc-steer/scripts/steer.py --vault-root <path> --section "..." --content "..."`
5. Run `/sdlc-kit:sync`

## Guardrails

- NEVER overwrite the entire file — only update specific sections
- NEVER remove existing rules unless explicitly asked
- Always show diff before applying
- Merge strategy: append to section if exists, create new section if not
