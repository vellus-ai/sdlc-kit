---
name: sdlc-kit:doc
description: Generate a document from any vault template
---

# sdlc-kit:doc

Generic document generation from any template in any phase.

## When to invoke

When you need to create a document that doesn't fit the specific skills (spec, prd, adr), e.g.:
- Test plan
- Runbook
- Release checklist
- Tech design (for non-SDD contexts)
- API design

## Flow

1. Ask: document type (which template to use)
2. Ask: document title
3. Ask: target phase folder
4. Fill template with context from CLAUDE.md and _INDEX.md
5. Save to appropriate phase folder
6. Run `/sdlc-kit:sync`

## Guardrails

- Only use templates from `assets/vault-tree/` — never invent new document types
- Always set complete frontmatter before saving
- Run sync after creation
