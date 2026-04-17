---
name: sdlc-kit:spec
description: Create a SDD spec trio for a feature — requirements, design, tasks
---

# sdlc-kit:spec

Creates a three-document Spec-Driven Development trio for a new feature.

## When to invoke

Before implementing ANY new feature. The trio is the entry point for all development work.

## Flow

1. Ask: feature name (becomes the folder slug)
2. Ask: which epic (optional)
3. Ask: target milestone (optional)
4. Generate `03-development/<slug>/requirements.md` using EARS notation
   - Present to user for review/approval
5. Generate `03-development/<slug>/design.md` with architecture approach
   - Present to user for review/approval  
6. Generate `03-development/<slug>/tasks.md` with implementation tasks
7. Run `/sdlc-kit:sync`

## Output structure

```
03-development/<slug>/
├── requirements.md   (EARS notation, user stories, acceptance criteria)
├── design.md         (overview, sequence diagram in Mermaid, component contracts)
└── tasks.md          (checkbox tasks with links back to requirements)
```

## Guardrails

- Never proceed to design.md without user approval of requirements.md
- Never generate tasks.md without user approval of design.md
- tasks.md MUST have wikilinks back to [[requirements]] and [[design]]
- Always run sync after completing the trio
