---
name: sdlc-status
description: |
  Use at the start of any session or when the user asks for a quick health
  check of the SDLC vault — typically `/sdlc-kit:status`, "check the vault",
  "ver o estado do projeto", "status do kit", "give me a project snapshot",
  "dashboard do SDLC", "qual a situação atual", "onde estão os ADRs", "quantas
  tasks abertas". Queries the SQLite tracker (`.sdlc-kit/db.sqlite`) for a
  single-shot read-only summary: total notes, notes by phase, open vs done
  tasks, ADRs accepted vs proposed. Complements `/sdlc-kit:sync` (which
  *refreshes* the index + MOCs); this one only *reports* what's already in
  the tracker. Also reads the first lines of `_INDEX.md` so the LLM can
  ground itself in the vault before running any other SDLC Kit skill. Emits
  a single JSON object on stdout. Never writes. If the DB is not yet
  initialized, asks the user to run `/sdlc-kit:init` first.
---

# sdlc-kit:status

Quick context snapshot of the vault. The **first thing** to run when you land
in a project that has a vault.

## When to invoke

- At the start of every session involving the vault, before any other SDLC
  Kit skill — the LLM needs to know *what exists* before offering to scaffold
  or transition artifacts.
- When the user asks *"qual é o estado do projeto"*, *"status", "check-in"*.
- Before a retrospective or milestone review — grounding numbers.

## When **not** to invoke

- If the user wants the index/MOCs *refreshed* (they may be stale) →
  `/sdlc-kit:sync`.
- If the user wants a traceability matrix → `/sdlc-kit:trace`.
- If the user wants blast-radius analysis of a specific note → `/sdlc-kit:impact`.

## Flow

1. Run `scripts/status.py --vault-root <path>` (or the CLI alias
   `sdlc-kit status`).
2. Read `.sdlc/_INDEX.md` first 50 lines so the LLM has the canonical
   navigation to cite.
3. Present the summary in the user's chat language.

## Output contract

Single JSON object on stdout:

```json
{
  "status": "ok",
  "vault": "/abs/path/to/.sdlc",
  "notes_total": 42,
  "notes_by_phase": {"00-steering": 3, "01-planning": 8, "02-architecture": 11, ...},
  "tasks": {"open": 12, "done": 30},
  "adrs": {"accepted": 7, "proposed": 2}
}
```

Exit codes: `0` ok, `1` DB not initialized (suggest `sdlc-kit init-db`),
`2` vault not found or invalid marker.

## Presentation guidelines

When presenting to the user, format as a compact table or bullet list
(NEVER raw JSON). Highlight anything unusual:

- `tasks.open > 10` → maybe worth prioritizing.
- `adrs.proposed > 0` → dangling decisions, cite them by slug from the
  DB or by asking `/sdlc-kit:adr list`.
- A phase with 0 notes → may indicate work not yet captured.

## Guardrails

**Never:**
- Write to the vault or the DB — this skill is strictly read-only.
- Auto-initialize the DB if it doesn't exist — ask the user to run
  `/sdlc-kit:init` or `sdlc-kit init-db` explicitly.
- Fabricate a fallback vault location when the marker is missing — surface
  the error clearly instead.
- Display raw JSON to the user — always format as a compact table or bullet
  list.

**Always:**
- Mirror the user's chat language in every report line.
- Group the snapshot by phase so the user can immediately spot gaps (a phase
  with 0 notes often means work not yet captured).
- Highlight anomalies proactively: `tasks.open > 10` (worth prioritizing),
  `adrs.proposed > 0` (dangling decisions — cite them by slug), stale
  `updated:` timestamps.
- Offer a follow-up skill when an anomaly shows up (`/sdlc-kit:sync` to
  refresh, `/sdlc-kit:adr list` to inspect dangling ADRs,
  `/sdlc-kit:impact <seed>` to analyze a specific note).

## Examples

**Healthy vault snapshot at session start:**
```
User: /sdlc-kit:status
AI:   [status.py --vault-root .sdlc]
AI:   "Vault snapshot — 42 notes
       | Phase             | Notes |
       |-------------------|-------|
       | 00-steering       |     3 |
       | 01-planning       |     8 |
       | 02-architecture   |    11 |
       | 04-specs          |    15 |
       | 07-retrospectives |     5 |
       Tasks: 12 open / 30 done. ADRs: 7 accepted / 2 proposed.
       Heads-up: 2 ADRs still in `proposed` — want me to list them with
       `/sdlc-kit:adr list`?"
```

**DB not initialized:**
```
User: /sdlc-kit:status
AI:   [status.py exits 1]
AI:   "The SQLite tracker isn't initialized yet — run
       `/sdlc-kit:init` to scaffold the vault, or `sdlc-kit init-db`
       if the vault exists but the DB is missing. I won't create it
       automatically."
```

**No vault in cwd:**
```
User: /sdlc-kit:status
AI:   [status.py exits 2 — marker not found]
AI:   "No `.sdlc-kit/marker.json` found walking up from cwd. Either
       you're outside a vault, or the vault was moved. Where should
       I look?"
```
