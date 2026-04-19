# sdlc-kit:milestone — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/milestone.md.tpl`.

## Flow

### Zero-arg: `/sdlc-kit:milestone`

1. Run `milestone.py --action list`.
2. Show one-line summary: `beta-launch — on-track (target: 2026-06-15)`.
3. Suggest next action (flag `at-risk`/`slipped`, nudge `planned` → `on-track`, scaffold new).

### `new`: `/sdlc-kit:milestone new <slug>`

1. **Derive slug.** If user gave free text ("Beta Launch"), propose `beta-launch` and confirm.
2. **Ask for target date** (optional but encouraged): `YYYY-MM-DD`.
3. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-milestone/scripts/milestone.py" \
     --vault-root "<vault>" --action scaffold \
     --slug <slug> --title "<Title>" \
     [--target-date YYYY-MM-DD]
   ```
4. **Run the interview** (below), section-by-section.
5. Stay in `planned` until work kicks off; invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb | Command |
|---|---|---|
| "kick off" / "start" | start | `--action transition --slug X --to on-track` |
| "at risk" / "slipping a bit" | at-risk | `--action transition --slug X --to at-risk` |
| "missed the date" | slip | `--action transition --slug X --to slipped` |
| "shipped" / "delivered" | done | `--action transition --slug X --to done` |
| "cancel" / "abandon" | cancel | `--action transition --slug X --to cancelled` |
| "back to planning" | reopen | `--action transition --slug X --to planned` |

Idempotent.

Before `done`, check `## Success criteria` and `## Aggregated scope`. If any
criterion checkbox is open, or any linked epic is not `done`, confirm.

Before `slipped` or `at-risk`, briefly recap what changed; offer to write a
`## Status` change-log line.

## The interview (LLM-driven, section by section)

Walk the template's sections, one focused question per section:

1. **Target date** — the single deadline. If `--target-date` used at scaffold, confirm; otherwise ask `YYYY-MM-DD` and write to `target_date:` frontmatter + body sentence.
2. **Status change log** — maintained manually. Template already has `{{DATE}} — initial status: planned`.
3. **Aggregated scope** — list epics as wikilinks: `[[<epic-slug>]] — <short status>`. Aim for 2–6 epics. Update each epic's `milestone:` frontmatter via Edit.
4. **Success criteria** — checkboxes. Should include "All linked epics are `done`" + 1–3 measurable criteria.
5. **Active risks** — risk / RAG / mitigation table. Per-risk RAG is qualitative; **not** the milestone's own status.
6. **External dependencies** — teams, vendors, compliance gates, infra.
7. **References** — associated PRDs as wikilinks.

Section-by-section only.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "milestones": [
    {"slug": "beta-launch", "path": "01-planning/milestone/beta-launch.md",
     "title": "Beta Launch", "status": "on-track", "owner": "Milton",
     "target_date": "2026-06-15", "updated": "2026-04-15"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "beta-launch",
  "milestone_path": "01-planning/milestone/beta-launch.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "beta-launch",
  "milestone_path": "01-planning/milestone/beta-launch.md",
  "previous_status": "planned", "new_status": "on-track",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Overwrite without `--force` and explicit confirmation.
- Rewrite body in one Edit call.
- Auto-derive status from dates or epic completion.
- Auto-promote to `done` — require explicit approval; flag open criteria / undone epics.
- Fabricate content.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md`.

**Always:**
- Mirror user's chat language.
- Run `--action list` first.
- Confirm slug before scaffolding.
- Offer `--target-date` when user knows it; don't invent.
- Invoke `/sdlc-kit:sync` after scaffold or transition.
- Keep aggregated scope to 2–6 epics.
- Link up: epic `milestone:` frontmatter, PRD under `## References`.

## Examples

**Fresh milestone with known target date:**
```
User: /sdlc-kit:milestone new "Beta Launch" 2026-06-15
AI:   "Proposed slug: `beta-launch`. Target 2026-06-15. Keep both?"
User: yes
AI:   [scaffold --target-date 2026-06-15]
AI:   "Target date set. **Aggregated scope** — which epics?"
User: login-overhaul, billing-rewrite
AI:   [Edit: write wikilinks under Aggregated scope]
AI:   [Edit each epic's frontmatter: milestone: "beta-launch"]
…
AI:   "Staying in `planned`. Tell me when work kicks off." [/sdlc-kit:sync]
```

**Mid-flight degradation:**
```
User: o beta-launch está em risco — billing-rewrite escorregou 2 semanas
AI:   [transition --to at-risk][/sdlc-kit:sync]
AI:   "✓ at-risk. Quer que eu anote a razão no log de `## Status`?"
User: sim
AI:   [Edit: append `2026-04-17 — at-risk (billing-rewrite slipped 2 weeks)`]
```

**Closing with pending epic:**
```
User: /sdlc-kit:milestone done beta-launch
AI:   "Antes de fechar:
       - Success criteria: 2 em aberto.
       - [[billing-rewrite]] ainda in-progress.
       Ainda marco como `done`?"
User: vamos resolver antes
AI:   [does not transition]
```

## See also

- `scripts/milestone.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/milestone.md.tpl`.
- `/sdlc-kit:prd`, `/sdlc-kit:epic`, `/sdlc-kit:spec`, `/sdlc-kit:sync`.
