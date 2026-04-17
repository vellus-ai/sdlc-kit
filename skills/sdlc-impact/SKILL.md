---
name: sdlc-kit:impact
description: Analyze the impact of changing a concept across the entire vault
---

# sdlc-kit:impact

Searches all Markdown files in the vault for a term or concept and reports which documents reference it, enabling impact analysis before renaming, refactoring, or deprecating.

## When to invoke

When planning to rename a domain concept, deprecate a component, change an API contract, or understand the blast radius of any significant change.

## Flow

1. Ask: term or concept to search for
2. Search all `.md` files in the vault (case-insensitive, excludes `.sdlc-kit/`)
3. Return a report with: file path, occurrence count, and first matching snippet
4. Optionally: the user can then decide which files need updating

## Guardrails

- Read-only operation — never modifies any file
- Excludes `.sdlc-kit/` directory (internal metadata)
- Snippets are trimmed to 100 characters to keep output scannable
- Term search is literal (not regex) and case-insensitive
