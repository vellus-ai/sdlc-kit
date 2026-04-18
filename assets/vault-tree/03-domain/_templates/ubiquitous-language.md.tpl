---
type: domain-ubiquitous-language
title: "Ubiquitous Language — {{PROJECT_NAME}}"
slug: "ubiquitous-language"
status: draft
phase: 03
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-domain
owner: "{{OWNER}}"
tags: [domain, ddd, glossary]
---

# Ubiquitous Language — {{PROJECT_NAME}}

> _(Living glossary of domain terms — a term can have different meanings in different contexts.)_

## How to use

- Use these terms **exactly** in code, documentation and conversations.
- If a term means different things in different contexts, document both under the same term with the **Context** column.
- When introducing a new concept, add it here before using in code.

## Glossary

### <Term A>

- **Definition:** <one clear sentence>.
- **Context where it applies:** <Context A>
- **Example:** <concrete sentence using the term>.
- **Don't confuse with:** <nearby term and why it's different>.

### <Term B>

- **Definition (in Context A):** <definition>.
- **Definition (in Context B):** <different definition>.
- **Example:** <concrete sentence>.

### <Term C>

- **Definition:** <definition>.
- **Context where it applies:** <Context A, Context B>
- **Rejected synonyms:** <terms that seem equivalent but should NOT be used>.

## Language antipatterns

- **Using generic "user"** when the domain distinguishes `Buyer`, `Seller`, `Operator`.
- **Mixing terms from different contexts** without explicit translation.
- **Inventing synonyms** instead of reusing already-defined terms.

## References

- [[context-map]] — contexts map
- [[_INDEX]] — global index
