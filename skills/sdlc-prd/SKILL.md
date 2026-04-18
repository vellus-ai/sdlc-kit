---
name: sdlc-prd
description: |
  Use when the user wants to create, review, or transition a Product
  Requirements Document (PRD) — the top-level "what + for whom" doc for an
  initiative. English triggers: `/sdlc-kit:prd`,
  `/sdlc-kit:prd new <title>`, `/sdlc-kit:prd list`,
  `/sdlc-kit:prd promote <slug>`, `/sdlc-kit:prd archive <slug>`,
  "start a PRD for X", "define product requirements for Y",
  "register a new initiative", "ship the PRD", "archive this initiative".
  pt-BR triggers: "iniciar um PRD para X",
  "definir requisitos de produto para Y", "registrar uma nova iniciativa",
  "lançar o PRD", "arquivar essa iniciativa". Co-authored by a duo of expert
  personas: a **Senior Engineer** (feasibility, testable KPIs, implementation
  risk) and an **Architect** (scope boundaries, cross-initiative
  dependencies, architectural implications). Each PRD lives at
  `01-planning/prd/<slug>.md`, one file per initiative. The script does
  deterministic file ops only — listing, scaffolding from
  `01-planning/_templates/prd.md.tpl`, and status transitions
  (draft → active → shipped → archived). The LLM drives the content
  interview section-by-section via Edit/Write, mirroring the user's chat
  language. After scaffold or transition, invokes `/sdlc-kit:sync` so
  `_INDEX.md` and `01-planning/_MOC.md` reflect the change. Do not invoke to
  record a technical decision (`/sdlc-kit:adr`), to write functional specs
  for a feature (`/sdlc-kit:spec`), or to create epics/milestones
  (`/sdlc-kit:epic` or `/sdlc-kit:milestone`).
---

# sdlc-kit:prd

Materializes and matures Product Requirements Documents under `01-planning/prd/`.

---

## What a PRD is (and isn't)

| PRD is… | PRD isn't… |
|---|---|
| One initiative, one file (`01-planning/prd/<slug>.md`) | A feature-level spec (use `/sdlc-kit:spec`) |
| The *what* and *for whom*, plus hypotheses, KPIs, scope boundaries | The *how* — no architecture, no API contracts |
| Linked to epics, ADRs, and the product vision (`00-steering/product.md`) | A to-do list of tasks (use `/sdlc-kit:task`) |
| Signed off by the product owner when it flips to `active` | An immutable record — promote/archive freely as reality shifts |

Statuses form a lifecycle: `draft` → `active` → `shipped` → `archived`.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:prd`, `/sdlc-kit:prd new <title>`, `/sdlc-kit:prd list`, `/sdlc-kit:prd promote <slug>`, `/sdlc-kit:prd archive <slug>`.
- The user says "register a new initiative", "start a PRD for X", "write the product requirements for Y", "ship the PRD", "archive this initiative" — or equivalent phrasing in any other language.
- `/sdlc-kit:steer product` just finished and the user wants to turn vision into its first concrete initiative.

**Do not** invoke when:

- The user wants an architecture decision → `/sdlc-kit:adr`.
- The user wants feature-level requirements/design/tasks → `/sdlc-kit:spec`.
- The user wants epics or milestones → `/sdlc-kit:epic` / `/sdlc-kit:milestone`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/prd.md.tpl`. If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg / list: `/sdlc-kit:prd` or `/sdlc-kit:prd list`

1. Run `prd.py --action list`. Parse the JSON `prds` array.
2. Show the user a compact table: `slug | status | title | updated`.
3. If empty, offer: "No PRDs yet. Want to start one with `/sdlc-kit:prd new <title>`?"
4. Otherwise, offer next actions: open any draft, promote a mature draft, or create a new one.

### New PRD: `/sdlc-kit:prd new <title>`

1. **Derive the slug.** Propose a slug from the title (lowercase ASCII, hyphen-separated) and confirm with the user. Let them override if they prefer a shorter or more specific slug.
2. **Status check.** Run `--action list` first so you know whether the slug collides with an existing PRD.
3. **Collision?** If `<slug>.md` already exists, ask whether to open the existing PRD, pick a different slug, or overwrite (then pass `--force`).
4. **Scaffold.** Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-prd/scripts/prd.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<owner>"]
   ```
   The script fills placeholders (`{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`) from arguments + `marker.json`.
5. **Interview** (see below).

### The interview (LLM-driven, section by section)

Walk the template sections in this order and ask one focused question per section. Edit in place via the Edit tool — do not rewrite the entire file at once. Match the user's active conversation language when speaking to them; template section headings remain in whatever language the template ships with.

1. **Context** — current situation and what is changing (2–4 paragraphs).
2. **Problem** — one concrete, measurable problem statement: who, how often, what impact.
3. **Hypotheses** — 1–3 testable hypotheses, each with the metric or experiment that validates it.
4. **Scope** — in-scope vs. out-of-scope. Out-of-scope items matter as much as in-scope ones.
5. **KPIs** — 1–3 metrics with baseline, target, and deadline.
6. **Risks** — top 2–3 risks with probability, impact, and mitigation.
7. **Schedule** — kickoff, milestones, GA. Placeholder dates are acceptable when unresolved.
8. **Stakeholders** — sponsor, product owner, tech lead, design lead.

Keep it to **≤8 questions**. If the user doesn't have an answer for a section, leave the template placeholder intact and offer to revisit later.

### Transition: `/sdlc-kit:prd promote|ship|archive <slug>`

Map the verb → target status and run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-prd/scripts/prd.py" \
  --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|active|shipped|archived>"
```

| Verb | Target status | When to use |
|---|---|---|
| `promote` | `active` | Draft is reviewed, owner signed off |
| `ship` | `shipped` | Initiative reached GA / delivered its KPIs |
| `archive` | `archived` | Cancelled, deprioritized, or superseded |
| `reopen` | `draft` | Needs more work; active status was premature |

No-op if the PRD is already at the target status (the script returns `previous_status == new_status` and writes nothing — keeps git clean).

### Sync

After every scaffold or transition, invoke `/sdlc-kit:sync` so `_INDEX.md` and `01-planning/_MOC.md` reflect the change.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "prds": [
    {"slug": "auth-login", "path": "01-planning/prd/auth-login.md",
     "title": "Autenticação com Google", "status": "active",
     "owner": "Milton", "updated": "2026-04-17"}
  ],
  "count": 1,
  "errors": []
}

// --action scaffold
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "slug": "checkout-v2",
  "prd_path": "01-planning/prd/checkout-v2.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "auth-login",
  "prd_path": "01-planning/prd/auth-login.md",
  "previous_status": "draft",
  "new_status": "active",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug, target exists, PRD not found, invalid status) · `2` fatal (permission denied, IO, missing template).

---

## Guardrails

**Never:**
- Overwrite an existing PRD without `--force` and explicit user confirmation.
- Rewrite the entire PRD in one Edit call — section-by-section only.
- Auto-promote to `active` — always require explicit user approval. `active` means the product owner signed off.
- Fabricate KPIs, hypotheses, or stakeholder names. Prefer leaving the template placeholder with a note to revisit.
- Silently rename a PRD. If the slug needs to change, archive the old one and scaffold a new one so the wikilink history stays traceable.

**Always:**
- Match the user's active conversation language.
- Run `--action list` before scaffold so you can spot slug collisions early.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- Surface the generated file path in the final report so the user can open it.
- When transitioning to `active` or `shipped`, remind the user which section the downstream artefacts (epics, specs, ADRs) should link back to.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**New initiative from scratch:**
```
User: /sdlc-kit:prd new Checkout v2
AI:   Proposed slug: `checkout-v2`. OK, or would you rather something else?
User: ok
AI:   [list] no collision. Scaffolding…
AI:   [scaffold] created 01-planning/prd/checkout-v2.md
AI:   "Let's fill this in section by section. Starting with **Context** — in
       2-4 paragraphs, describe the current situation and what is changing."
User: <answer>
AI:   [Edit tool: replace Context section]
AI:   "Next: **Problem**. Who feels it, how often, what's the impact?"
…
AI:   "All 8 sections filled. Promote to `status: active`? (y/n)"
User: not yet — I want to review with the PO first
AI:   "No problem. Leaving it as `draft`. When ready: `/sdlc-kit:prd promote checkout-v2`."
```

**Listing PRDs:**
```
User: /sdlc-kit:prd list
AI:   | slug        | status   | title                        | updated     |
      |-------------|----------|------------------------------|-------------|
      | auth-login  | active   | Google sign-in               | 2026-04-17  |
      | checkout-v2 | draft    | New checkout flow            | 2026-04-17  |
AI:   "2 PRDs. Want to continue work on a draft, or start a new one?"
```

**Promoting a mature draft:**
```
User: /sdlc-kit:prd promote checkout-v2
AI:   [list] found checkout-v2 (draft).
AI:   "Confirm promoting checkout-v2 draft→active? Did the PO sign off?"
User: yes, PO approved yesterday
AI:   [transition draft→active] [/sdlc-kit:sync]
AI:   "✓ 01-planning/prd/checkout-v2.md is now active. Suggested next step:
       `/sdlc-kit:epic new <first-epic-of-this-initiative>`."
```

**Idempotent transition:**
```
User: /sdlc-kit:prd promote auth-login
AI:   [list] auth-login already active — nothing to do. Skipping sync.
```

---

## See also

- `scripts/prd.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/prd.md.tpl` — canonical template.
- `/sdlc-kit:steer product` — the upstream product vision a PRD should align with.
- `/sdlc-kit:epic` — decompose an active PRD into epics.
- `/sdlc-kit:spec` — feature-level specs that refine PRD requirements.
- `/sdlc-kit:sync` — always invoked after PRD edits.
