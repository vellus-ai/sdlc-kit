---
name: sdlc-status
description: Esta skill deve ser usada para obter um resumo JSON da saúde do vault SDLC, ou quando o usuário invoca /sdlc-kit:status. Retorna contagem de notas por fase, eventos recentes, worktrees ativos e alertas. Útil para check-in rápido do estado do projeto.
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
