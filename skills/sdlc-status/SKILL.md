---
name: sdlc-kit:status
description: Show vault health summary — quick context for the LLM at session start
---

# sdlc-kit:status

Provides a quick context snapshot of the vault for the LLM.

## When to invoke

At the start of any work session involving this project. Before any other skill.

## Flow

1. Run `sdlc-kit status` (the CLI command)
2. Also read `.sdlc/_INDEX.md` (first 50 lines)
3. Present as formatted summary

## Output

Present the status as:
- Vault location
- Total documents by phase
- Open tasks vs done
- ADRs: how many accepted, how many proposed
- Last sync timestamp
- Any anomalies from last sync

## Guardrails

- Read-only operation — no writes
- If vault not found, ask user to run `/sdlc-kit:init`
