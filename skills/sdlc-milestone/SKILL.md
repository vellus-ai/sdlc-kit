---
name: sdlc-kit:milestone
description: Create milestones with RAG status and deadline tracking
---

# sdlc-kit:milestone

Manages milestones with RAG (Red/Amber/Green) health status.

## When to invoke
- When defining a delivery milestone
- When checking milestone health

## RAG Rules
- 🟢 Green: ≥80% epics done AND target date not passed
- 🟡 Amber: <80% done OR within 7 days of target
- 🔴 Red: overdue OR <40% done with <14 days remaining

## Flow
1. Ask: milestone name, target date, linked epics
2. Ask: completion criteria (2-3 items)
3. Generate entry in `03-development/MILESTONES.md`
4. Run `/sdlc-kit:sync`
