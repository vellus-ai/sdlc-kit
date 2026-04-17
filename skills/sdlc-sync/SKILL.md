---
name: sdlc-kit:sync
description: Run the vault librarian — validate frontmatter, update MOCs and INDEX
---

# sdlc-kit:sync

The vault librarian. Runs after any vault write to keep everything consistent.

## When to invoke

- Automatically (via PostToolUse hook after any vault file edit)
- Manually after bulk operations
- At the start of a session to verify vault health

## Flow

1. Run `python skills/sdlc-sync/scripts/sync.py --vault-root <path>`
2. Report: docs scanned, anomalies found
3. If anomalies found, describe each one and suggest fixes

## Output format

```json
{
  "status": "ok",
  "scanned": 12,
  "updated_mocs": ["01-planning", "03-development"],
  "anomalies": [
    {"type": "missing_frontmatter_field", "file": "01-planning/PRD.md", "field": "updated"},
    {"type": "no_wikilinks", "file": "03-development/tasks.md"}
  ]
}
```

## Guardrails

- Never delete files — only reads and updates MOC/INDEX
- _INDEX.md is regenerated, not edited
- Anomalies are reported, not auto-fixed (user decides)
