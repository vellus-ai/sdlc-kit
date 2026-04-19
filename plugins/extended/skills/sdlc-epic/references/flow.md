# sdlc-kit:epic — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/epic.md.tpl`.

## Flow

### Zero-arg: `/sdlc-kit:epic`

1. Run `epic.py --action list`.
2. Show one-line summary per epic: `login-overhaul — in-progress (milestone: q2-2026)`.
3. Suggest next action (start a planned, check in on in-progress, scaffold new).

### `new`: `/sdlc-kit:epic new <slug>`

1. **Derive slug.** If user gave free text ("login overhaul"), propose `login-overhaul` and confirm. Slug is filename + wikilink key — hard to change later.
2. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-epic/scripts/epic.py" \
     --vault-root "<vault>" --action scaffold --slug <slug> --title "<Title>"
   ```
3. **Run the interview** (below), section-by-section.
4. Stay in `planned` until work kicks off; invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb | Command |
|---|---|---|
| "kick off" / "start" | start | `--action transition --slug X --to in-progress` |
| "done" / "shipped" | done | `--action transition --slug X --to done` |
| "cancel" / "abandon" | cancel | `--action transition --slug X --to cancelled` |
| "reopen" | reopen | `--action transition --slug X --to planned` |

Idempotent.

Before `done`, check `## Acceptance criteria`. If open checkboxes remain,
confirm before silently overriding.

## The interview (LLM-driven, section by section)

Walk the template's sections, one focused question per section:

1. **Objective** — concrete outcome this epic delivers (1 paragraph).
2. **Business value** — which PRD KPI does this move? Wikilink PRD via `[[<prd-slug>]]`.
3. **Stories** — `As <persona>, I want <action>, so that <benefit>`. 3–8 stories; more suggests splitting. Note which deserve their own spec trio.
4. **Scope — Included / Excluded** — explicit in-scope and out-of-scope.
5. **Acceptance criteria** — checkboxes; ideally measurable.
6. **Estimate** — size (S/M/L/XL) or story points; duration in sprints/weeks.
7. **Dependencies** — external teams, other epics, infra.

Update frontmatter `prd:` and `milestone:` via Edit when named. Don't fabricate.

Edit section-by-section — never rewrite the whole file at once.

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "epics": [
    {"slug": "login-overhaul", "path": "01-planning/epic/login-overhaul.md",
     "title": "Login Overhaul", "status": "in-progress",
     "owner": "Milton", "prd": "auth-modernization",
     "milestone": "q2-2026", "updated": "2026-04-15"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "login-overhaul",
  "epic_path": "01-planning/epic/login-overhaul.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "login-overhaul",
  "epic_path": "01-planning/epic/login-overhaul.md",
  "previous_status": "planned", "new_status": "in-progress",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Overwrite without `--force` and explicit user confirmation.
- Rewrite body in one Edit call.
- Auto-promote to `done` — require explicit approval; flag open acceptance-criteria.
- Fabricate content — leave template placeholders.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md`.

**Always:**
- Mirror user's chat language.
- Run `--action list` first.
- Confirm slug before scaffolding.
- Invoke `/sdlc-kit:sync` after scaffold or transition.
- Keep stories to 3–8 per epic; suggest splitting if more.
- Link up: `prd:`, `milestone:`, stories to spec trios via `[[<feature>-requirements]]`.

## Examples

**Fresh epic from a just-approved PRD:**
```
User: /sdlc-kit:epic new "Login Overhaul"
AI:   "Proposed slug: `login-overhaul`. Keep it?"
User: yes
AI:   [scaffold] created 01-planning/epic/login-overhaul.md.
AI:   "Let's fill this in section by section. First — **Objective**…"
User: <answer>
AI:   [Edit: replace Objective]
AI:   "Next — **Business value**: which PRD KPI? Which PRD is this under?"
User: auth-modernization
AI:   [Edit: set prd: "auth-modernization"; fill Business value]
…
AI:   "All sections filled. Staying in `planned`. Tell me when work kicks off."
AI:   [/sdlc-kit:sync]
```

**Mid-flight status change:**
```
User: o time começou a mexer no login-overhaul
AI:   [transition --to in-progress] [/sdlc-kit:sync]
```

**Closing with open checkboxes:**
```
User: /sdlc-kit:epic done login-overhaul
AI:   "Encontrei 2 itens abertos em `## Acceptance criteria`:
       - [ ] Legacy password login removido do frontend.
       - [ ] 99% de logins migrados.
       Ainda marco como `done`, ou prefere fechar antes?"
User: vamos fechar antes
AI:   [does not transition]
```

## See also

- `scripts/epic.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/epic.md.tpl`.
- `/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:milestone`, `/sdlc-kit:sync`.
