---
name: sdlc-review
description: Esta skill deve ser usada para rodar checklist de completude antes de PR, ou quando o usuário invoca /sdlc-kit:review. Verifica: specs trios SDD completos, frontmatter válido, TASKS.md atualizado, ADRs não travados em review. Retorna JSON estruturado.
---

# sdlc-kit:review

Validates that a phase or spec is complete before moving forward.

## When to invoke
- Before closing a sprint
- Before moving a feature from development to testing
- As a gate before creating a PR

## Checks
1. All spec trios have requirements.md, design.md, tasks.md
2. All documents have complete frontmatter
3. All _MOC.md files are up to date
4. No ADRs stuck in "proposed" for >7 days
5. TASKS.md exists with at least 1 entry

## Output
JSON with pass/fail per check and list of issues.
