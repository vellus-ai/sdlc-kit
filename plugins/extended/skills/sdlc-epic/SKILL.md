---
name: sdlc-epic
description: |
  Use when the user wants to create, list, or change the status of an epic —
  a large deliverable decomposed from a PRD that groups related stories (each
  often becoming a spec trio under `04-specs/`). English triggers:
  `/sdlc-kit:epic`, `/sdlc-kit:epic new <slug>`, `/sdlc-kit:epic start <slug>`,
  `/sdlc-kit:epic done <slug>`, `/sdlc-kit:epic cancel <slug>`,
  `/sdlc-kit:epic list`, "start an epic for X",
  "the auth epic is in progress", "mark the onboarding epic as done",
  "cancel the legacy-billing epic". pt-BR triggers: "criar um epic para X",
  "o epic de auth está em andamento", "marcar o epic de onboarding como done",
  "cancelar o epic legacy-billing". Co-authored by a duo of expert personas:
  a **Product Manager** (owns objective, business value, stories, scope) and
  a **Tech Lead** (owns acceptance criteria, estimate, dependencies,
  story-to-spec decomposition). Creates one file per epic at
  `01-planning/epic/<slug>.md` from `01-planning/_templates/epic.md.tpl`.
  The script handles deterministic operations only (list / scaffold /
  transition); the LLM drives the interview and section-by-section editing
  via Edit, mirroring the user's chat language. Lifecycle: `planned` →
  `in-progress` → `done`, with `cancelled` as a terminal option. Always
  invokes `/sdlc-kit:sync` after any change. Do not invoke for individual
  feature specs (`/sdlc-kit:spec`), initiative-level product scope
  (`/sdlc-kit:prd`), or delivery windows grouping multiple epics
  (`/sdlc-kit:milestone`).
---

# sdlc-kit:epic

Materializes and matures epics — the planning layer between a PRD (what and why for an initiative) and specs (what and how for a feature).

---

## Where epics fit

```
PRD (initiative-level scope)
  └─ Epic (a large deliverable within the PRD)
        ├─ Story US-01 → Spec trio in 04-specs/<feature-a>/
        ├─ Story US-02 → Spec trio in 04-specs/<feature-b>/
        └─ Story US-03
  └─ Milestone (a delivery window grouping one or more epics)
```

One file per epic at `01-planning/epic/<slug>.md`. Stories live as bullets inside the epic's `## Stories` section; they're not separate files.

---

## Lifecycle

| Status | Meaning |
|---|---|
| `planned` | Scoped and in the backlog, not started. |
| `in-progress` | Active — at least one story in flight. |
| `done` | All acceptance criteria met. |
| `cancelled` | Abandoned — kept for history, not deleted. |

Start in `planned`. Move forward one step at a time; `cancelled` is reachable
from any state.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:epic`, `/sdlc-kit:epic new <slug>`, `/sdlc-kit:epic list`, `/sdlc-kit:epic {start|done|cancel|reopen} <slug>`.
- The user says "start an epic for X", "the Y epic is in progress", "mark Z as done", "cancel the W epic" — or equivalent phrasing in any other language.
- A PRD was just approved and the user wants to break it into epics.

**Do not** invoke when:

- The user wants a feature-level spec → use `/sdlc-kit:spec`.
- The user wants initiative-level product scope → use `/sdlc-kit:prd`.
- The user wants a delivery window grouping epics → use `/sdlc-kit:milestone`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/epic.md.tpl`. If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg: `/sdlc-kit:epic`

1. Run `epic.py --action list`. Parse the JSON `epics` array.
2. Show the user a one-line summary per epic: `login-overhaul — in-progress (milestone: q2-2026)`.
3. Suggest next action:
   - If any epic is `planned` → "Want to start the interview / kick off `<slug>`?"
   - If any `in-progress` has stale `updated:` → "Check in on `<slug>`?"
   - Else → "Want to scaffold a new epic? Give me the name."

### `new`: `/sdlc-kit:epic new <slug>` (or natural language)

1. **Derive slug.** If the user gave free text (e.g. "login overhaul"), propose a slug (`login-overhaul`) and confirm before scaffolding. The slug is the filename and the wikilink key — hard to change later.
2. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-epic/scripts/epic.py" \
     --vault-root "<vault>" --action scaffold --slug <slug> --title "<Title>"
   ```
3. **Run the interview** (see below), section-by-section.
4. When the user is happy with the initial draft (it stays `planned` until work actually starts), invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb heard | Command |
|---|---|---|
| "kick off" / "start" / "we're working on it" | start | `--action transition --slug X --to in-progress` |
| "done" / "shipped" / "close it" | done | `--action transition --slug X --to done` |
| "cancel" / "abandon" / "drop it" | cancel | `--action transition --slug X --to cancelled` |
| "reopen" / "back to planning" | reopen | `--action transition --slug X --to planned` |

Transitions are **idempotent** — re-running with the current status writes nothing.

Before marking `done`, check the `## Acceptance criteria` section of the epic file. If open checkboxes remain, ask the user to confirm they really want to move on despite the pending items (don't silently override).

---

## The interview (LLM-driven, section by section)

Walk the template's sections in order. One focused question per section, always in the user's active conversation language:

1. **Objective** — what concrete outcome does this epic deliver? (1 paragraph.)
2. **Business value** — which PRD KPI does this move, and how? Link the PRD via wikilink (`[[<prd-slug>]]`).
3. **Stories** — elicit each as `As <persona>, I want <action>, so that <benefit>`. For stories that deserve their own spec trio, note it and offer to run `/sdlc-kit:spec new` afterwards. Aim for 3–8 stories; more suggests the epic should split.
4. **Scope — Included / Excluded** — explicit in-scope list and explicit out-of-scope list. Forces conversations about ambiguity early.
5. **Acceptance criteria** — checkboxes the epic must tick to be "done". Ideally measurable.
6. **Estimate** — size (S/M/L/XL) or story points; expected duration in sprints or weeks.
7. **Dependencies** — external teams, other epics, infra.

Update the frontmatter `prd:` and `milestone:` fields via Edit when the user names them. Do not fabricate values — leave empty if the user doesn't have an answer yet.

Do not rewrite the file in one Edit call — section-by-section only.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "epics": [
    {
      "slug": "login-overhaul",
      "path": "01-planning/epic/login-overhaul.md",
      "title": "Login Overhaul",
      "status": "in-progress",
      "owner": "Milton",
      "prd": "auth-modernization",
      "milestone": "q2-2026",
      "updated": "2026-04-15"
    }
  ],
  "count": 1,
  "errors": []
}

// --action scaffold
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "slug": "login-overhaul",
  "epic_path": "01-planning/epic/login-overhaul.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "login-overhaul",
  "epic_path": "01-planning/epic/login-overhaul.md",
  "previous_status": "planned",
  "new_status": "in-progress",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (missing arg, invalid slug, already exists, not found, invalid status) · `2` fatal (permission denied, IO, template missing).

---

## Guardrails

**Never:**
- Overwrite an existing epic file without `--force` and explicit user confirmation.
- Rewrite the epic body in one Edit call — always section-by-section.
- Auto-promote to `done` — always require explicit user approval, and flag open acceptance-criteria checkboxes before flipping.
- Fabricate content. Leave placeholders in the template for sections the user can't yet answer.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md` — those are managed by `/sdlc-kit:sync` and the user.

**Always:**
- Mirror the user's active conversation language.
- Run `--action list` before scaffold/transition so you know the current state.
- Confirm the slug with the user before scaffolding.
- Invoke `/sdlc-kit:sync` after scaffold or transition.
- Keep stories to 3–8 per epic; if more, suggest splitting.
- Link up: `prd:` to the PRD slug, `milestone:` to the milestone slug, stories to spec trios via `[[<feature>-requirements]]` wikilinks.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Fresh epic from a just-approved PRD:**
```
User: /sdlc-kit:epic new "Login Overhaul"
AI:   "Proposed slug: `login-overhaul`. Keep it?"
User: yes
AI:   [scaffold --slug login-overhaul --title "Login Overhaul"]
AI:   [scaffold] created 01-planning/epic/login-overhaul.md.
AI:   "Let's fill this in section by section. First — **Objective**: in one
       paragraph, what concrete outcome does this epic deliver?"
User: <answer>
AI:   [Edit: replace Objective section]
AI:   "Next — **Business value**: which PRD KPI does this move? I'll also
       link the PRD — which one is this under?"
User: auth-modernization
AI:   [Edit: set prd: "auth-modernization" in frontmatter; fill Business value]
…
AI:   "All sections filled. Staying in `planned` for now — tell me when work
       kicks off and I'll flip it to `in-progress`."
AI:   [/sdlc-kit:sync]
```

**Mid-flight status change:**
```
User: o time começou a mexer no login-overhaul
AI:   [transition --slug login-overhaul --to in-progress]
AI:   [/sdlc-kit:sync]
AI:   "✓ `login-overhaul` marcado como in-progress."
```

**Closing an epic with open checkboxes:**
```
User: /sdlc-kit:epic done login-overhaul
AI:   "Encontrei 2 itens abertos em `## Acceptance criteria`:
       - [ ] Legacy password login removido do frontend.
       - [ ] 99% de logins migrados.
       Ainda assim marco como `done`, ou prefere fechar esses itens antes?"
User: vamos fechar antes
AI:   [does not transition; leaves the user to edit the checkboxes]
```

**List overview:**
```
User: /sdlc-kit:epic
AI:   login-overhaul       — in-progress (milestone: q2-2026)
      billing-rewrite      — planned      (milestone: q3-2026)
      legacy-auth-sunset   — cancelled
AI:   "Want to kick off `billing-rewrite` or check in on `login-overhaul`?"
```

---

## See also

- `scripts/epic.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/epic.md.tpl` — canonical template (copied into each vault at init time).
- `/sdlc-kit:prd` — initiative-level product scope; epics decompose from a PRD.
- `/sdlc-kit:spec` — feature-level specs; each story typically becomes a spec trio.
- `/sdlc-kit:milestone` — delivery window grouping one or more epics.
- `/sdlc-kit:sync` — always invoked after epic edits.
