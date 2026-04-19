---
name: sdlc-milestone
description: |
  Use when the user wants to create, list, or change the status of a
  milestone — a delivery window that groups one or more epics toward a single
  target date, with RAG-style health (planned / on-track / at-risk / slipped
  / done). English triggers: `/sdlc-kit:milestone`,
  `/sdlc-kit:milestone new <slug>`, `/sdlc-kit:milestone start <slug>`,
  `/sdlc-kit:milestone at-risk <slug>`, `/sdlc-kit:milestone slip <slug>`,
  `/sdlc-kit:milestone done <slug>`, `/sdlc-kit:milestone cancel <slug>`,
  `/sdlc-kit:milestone list`, "create a milestone for Q2",
  "the beta-launch milestone is at risk",
  "mark the Q2 milestone as slipped",
  "we shipped the beta-launch milestone",
  "cancel the Q3-rewrite milestone". pt-BR triggers:
  "criar um milestone para o Q2", "o milestone beta-launch está em risco",
  "marcar o milestone Q2 como slipped", "entregamos o beta-launch",
  "cancelar o milestone Q3-rewrite". Driven by a **Program Manager**
  persona — owns the delivery window, qualitative RAG health call, and the
  portfolio view of which epics this milestone aggregates. Creates one file
  per milestone at `01-planning/milestone/<slug>.md` from
  `01-planning/_templates/milestone.md.tpl`. The script handles deterministic
  operations only (list / scaffold / transition) plus an optional
  `--target-date YYYY-MM-DD` at scaffold time; the LLM drives the interview
  (target date, aggregated epics, success criteria, active risks, external
  dependencies) section-by-section via Edit, mirroring the user's chat
  language. Lifecycle: `planned` → `on-track` → `done`, with degradation via
  `at-risk` → `slipped`, and `cancelled` as a terminal option from any
  state. RAG health is a qualitative call the user makes; the script does
  not auto-derive it from dates or completion percentages. Always invokes
  `/sdlc-kit:sync` after any change. Do not invoke for individual
  deliverables inside a milestone (`/sdlc-kit:epic`), initiative-level
  product scope (`/sdlc-kit:prd`), or feature-level specs
  (`/sdlc-kit:spec`).
---

# sdlc-kit:milestone

Materializes and matures milestones — the delivery window that groups one or
more epics toward a single target date.

---

## Where milestones fit

```
PRD (initiative-level scope)
  └─ Epic (a large deliverable within the PRD)
        ├─ Story US-01 → Spec trio in 04-specs/<feature-a>/
        └─ Story US-02 → Spec trio in 04-specs/<feature-b>/
  └─ Milestone (a delivery window grouping one or more epics)
```

A milestone is not a container of work — it is a **deadline**. Work lives in epics; the milestone aggregates which epics must ship by `target_date`.

One file per milestone at `01-planning/milestone/<slug>.md`. Epics reference their milestone via the `milestone:` frontmatter field.

---

## Lifecycle

| Status | Meaning |
|---|---|
| `planned` | Scoped with a target date, not yet started. |
| `on-track` 🟢 | Active and on schedule. |
| `at-risk` 🟡 | Active, schedule is threatened; needs attention. |
| `slipped` 🔴 | Target date missed or unreachable without action. |
| `done` | Delivered. |
| `cancelled` | Abandoned — kept for history, not deleted. |

Start in `planned`. Move forward through `on-track`/`at-risk`/`slipped`/`done` as the story unfolds; `cancelled` is reachable from any state. The degradation path (`on-track` → `at-risk` → `slipped`) is **qualitative** — it reflects the user's judgment, not a formula. The script never auto-flips a milestone; the
user decides.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:milestone`, `/sdlc-kit:milestone new <slug>`, `/sdlc-kit:milestone list`, `/sdlc-kit:milestone {start|at-risk|slip|done|cancel|reopen} <slug>`.
- The user says "create a milestone for Q2", "the Y milestone is at risk", "we shipped the Z milestone", "cancel the W milestone" — or equivalent phrasing in any other language.
- One or more epics are ready to be grouped under a delivery window.

**Do not** invoke when:

- The user wants a large deliverable → use `/sdlc-kit:epic`.
- The user wants initiative-level product scope → use `/sdlc-kit:prd`.
- The user wants a feature-level spec → use `/sdlc-kit:spec`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/milestone.md.tpl`.
   If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg: `/sdlc-kit:milestone`

1. Run `milestone.py --action list`. Parse the JSON `milestones` array.
2. Show the user a one-line summary per milestone:
   `beta-launch — on-track (target: 2026-06-15)`.
3. Suggest next action:
   - If any milestone is `at-risk` or `slipped` → "Want to talk through `<slug>` and decide next steps?"
   - If any `planned` is close to its target date → "Should we flip `<slug>` to `on-track`?"
   - Else → "Want to scaffold a new milestone? Give me the name and target date."

### `new`: `/sdlc-kit:milestone new <slug>` (or natural language)

1. **Derive slug.** If the user gave free text (e.g. "Beta Launch"), propose a slug (`beta-launch`) and confirm before scaffolding. The slug is the filename and the wikilink key — hard to change later.
2. **Ask for target date** (optional at scaffold time, but strongly encouraged): `YYYY-MM-DD`. If the user doesn't have one yet, scaffold without `--target-date` and fill the body later.
3. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-milestone/scripts/milestone.py" \
     --vault-root "<vault>" --action scaffold \
     --slug <slug> --title "<Title>" \
     [--target-date YYYY-MM-DD]
   ```
4. **Run the interview** (see below), section-by-section.
5. When the user is happy with the initial draft (it stays `planned` until work actively kicks off), invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb heard | Command |
|---|---|---|
| "kick off" / "start" / "we're on it" | start | `--action transition --slug X --to on-track` |
| "at risk" / "schedule is tight" / "slipping a bit" | at-risk | `--action transition --slug X --to at-risk` |
| "missed the date" / "can't hit it" / "it slipped" | slip | `--action transition --slug X --to slipped` |
| "shipped" / "delivered" / "done" | done | `--action transition --slug X --to done` |
| "cancel" / "abandon" / "drop it" | cancel | `--action transition --slug X --to cancelled` |
| "back to planning" / "reopen" | reopen | `--action transition --slug X --to planned` |

Transitions are **idempotent** — re-running with the current status writes nothing.

Before marking `done`, check the `## Success criteria` section of the milestone file and the `## Aggregated scope` list. If open criteria checkboxes remain, or any linked epic is not yet in `status: done`, ask the user to confirm they really want to move on despite the pending items (don't silently
override).

Before marking `slipped` or `at-risk`, the LLM should briefly recap what changed (which epic slipped, which dependency broke) and write a note under the `## Status` change log if the user offers one — the script only flips the frontmatter; rationale lives in the body.

---

## The interview (LLM-driven, section by section)

Walk the template's sections in order. One focused question per section, always in the user's active conversation language:

1. **Target date** — the single deadline this milestone commits to. If set at scaffold time via `--target-date`, confirm it; otherwise ask for `YYYY-MM-DD` and write it into the `target_date:` frontmatter field + the body sentence.
2. **Status change log** — at scaffold time, the template already has`{{DATE}} — initial status: planned`. As status flips later, the user may add lines here with rationale. Maintained manually; the script does not touch this section.
3. **Aggregated scope** — list the epics included in this milestone as wikilinks: `[[<epic-slug>]] — <short status>`. Aim for 2–6 epics; more suggests the milestone should split, fewer may mean it's really an epic. Update each epic's `milestone:` frontmatter via Edit when linking.
4. **Success criteria** — checkboxes the milestone must tick to be "done". Should include "All linked epics are in `status: done`" plus 1–3 measurable product/technical criteria.
5. **Active risks** — the risk / RAG / mitigation table. RAG here is a per-risk qualitative signal; it is **not** the milestone's own status. Keep to the risks that actually matter this cycle.
6. **External dependencies** — teams, vendors, compliance gates, infra the milestone depends on and does not control.
7. **References** — associated PRDs as wikilinks. The `[[_INDEX]]` line is already there — leave it alone.

Do not rewrite the file in one Edit call — section-by-section only.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "milestones": [
    {
      "slug": "beta-launch",
      "path": "01-planning/milestone/beta-launch.md",
      "title": "Beta Launch",
      "status": "on-track",
      "owner": "Milton",
      "target_date": "2026-06-15",
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
  "slug": "beta-launch",
  "milestone_path": "01-planning/milestone/beta-launch.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "beta-launch",
  "milestone_path": "01-planning/milestone/beta-launch.md",
  "previous_status": "planned",
  "new_status": "on-track",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (missing arg, invalid slug, invalid target date, already exists, not found, invalid status) · `2` fatal (permission denied, IO, template missing).

---

## Guardrails

**Never:**
- Overwrite an existing milestone file without `--force` and explicit user confirmation.
- Rewrite the milestone body in one Edit call — always section-by-section.
- Auto-derive the milestone's status from dates or epic completion counts — the user calls the RAG. The script only flips what the user tells it to.
- Auto-promote to `done` — always require explicit user approval, and flag open success-criteria checkboxes or not-yet-done linked epics before flipping.
- Fabricate content. Leave placeholders in the template for sections the user can't yet answer.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md` — those are managed by `/sdlc-kit:sync` and the user.

**Always:**
- Mirror the user's active conversation language.
- Run `--action list` before scaffold/transition so you know the current state.
- Confirm the slug with the user before scaffolding.
- Offer to set `--target-date` at scaffold time when the user knows it; don't
  invent one.
- Invoke `/sdlc-kit:sync` after scaffold or transition.
- Keep aggregated scope to 2–6 epics; if more, suggest splitting the milestone.
- Link up: each epic's `milestone:` frontmatter to this milestone's slug,
  associated PRD via wikilink under `## References`.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Fresh milestone with a known target date:**
```
User: /sdlc-kit:milestone new "Beta Launch" 2026-06-15
AI:   "Proposed slug: `beta-launch`. Target date 2026-06-15. Keep both?"
User: yes
AI:   [scaffold --slug beta-launch --title "Beta Launch" --target-date 2026-06-15]
AI:   [scaffold] created 01-planning/milestone/beta-launch.md.
AI:   "Target date set. Let's fill this in. First — **Aggregated scope**:
       which epics does this milestone ship? I'll link them."
User: login-overhaul, billing-rewrite
AI:   [Edit: write `- [[login-overhaul]] — in-progress` and
              `- [[billing-rewrite]] — planned` under Aggregated scope]
AI:   [Edit each epic's frontmatter: milestone: "beta-launch"]
AI:   "Next — **Success criteria**: beyond both epics being done, what
       measurable product/technical signals tell us this milestone delivered?"
…
AI:   "Draft saved, staying in `planned`. Tell me when work kicks off and
       I'll flip it to `on-track`."
AI:   [/sdlc-kit:sync]
```

**Mid-flight degradation:**
```
User: o beta-launch está em risco — o billing-rewrite escorregou duas semanas
AI:   [transition --slug beta-launch --to at-risk]
AI:   [/sdlc-kit:sync]
AI:   "✓ `beta-launch` marcado como at-risk. Quer que eu anote a razão
       (billing-rewrite atrasou 2 semanas) no log de `## Status`?"
User: sim
AI:   [Edit: append `2026-04-17 — at-risk (billing-rewrite slipped 2 weeks)`
              to the Status change log]
```

**Closing a milestone with pending epic:**
```
User: /sdlc-kit:milestone done beta-launch
AI:   "Antes de fechar, verifiquei:
       - `## Success criteria` tem 2 itens em aberto.
       - `[[billing-rewrite]]` ainda está em `in-progress`.
       Ainda assim marco como `done`, ou prefere resolver antes?"
User: vamos resolver antes
AI:   [does not transition; leaves the user to close the epic and criteria]
```

**List overview:**
```
User: /sdlc-kit:milestone
AI:   beta-launch          — on-track   (target: 2026-06-15)
      q3-rewrite           — planned    (target: 2026-09-30)
      legacy-auth-sunset   — cancelled
AI:   "Want to check in on `beta-launch` or scope `q3-rewrite`?"
```

---

## See also

- `scripts/milestone.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/milestone.md.tpl` — canonical template (copied into each vault at init time).
- `/sdlc-kit:prd` — initiative-level product scope.
- `/sdlc-kit:epic` — large deliverables grouped by a milestone.
- `/sdlc-kit:spec` — feature-level specs; each story typically becomes a spec
  trio.
- `/sdlc-kit:sync` — always invoked after milestone edits.
