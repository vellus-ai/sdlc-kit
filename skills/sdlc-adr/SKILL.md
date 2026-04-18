---
name: sdlc-adr
description: |
  Use when the user wants to record, review, or transition an Architecture
  Decision Record (ADR) — one file per decision, numbered monotonically under
  `02-architecture/adr/`. English triggers: `/sdlc-kit:adr`,
  `/sdlc-kit:adr new <title>`, `/sdlc-kit:adr list`,
  `/sdlc-kit:adr accept <id>`, `/sdlc-kit:adr supersede <old> --by <new>`,
  "record a decision", "write an ADR for X", "accept ADR 3",
  "deprecate that choice", "supersede the old DB decision". pt-BR triggers:
  "registrar uma decisão", "escrever um ADR para X", "aceitar o ADR 3",
  "deprecar aquela escolha", "substituir a decisão antiga de banco".
  Co-authored by a duo of expert personas: a **Senior Software Engineer**
  (operational consequences, implementation plan) and a **Software Architect**
  (alternatives considered, pattern fit, consistency with existing ADRs). The
  script does deterministic file ops only — listing, scaffolding from
  `02-architecture/_templates/adr.md.tpl` with auto-numbered filenames
  (`ADR-NNNN-<slug>.md`, 4-digit zero-padded, max existing + 1), and MADR
  lifecycle transitions (proposed → accepted/rejected → superseded/deprecated).
  The LLM drives the content interview (context, decision, alternatives,
  consequences) section-by-section via Edit/Write, mirroring the user's chat
  language. Numbers are never reused and filenames never renamed — history
  stays stable. After scaffold or transition, invokes `/sdlc-kit:sync` so MOCs
  and `_INDEX.md` reflect the change. Do not invoke for product requirements
  (`/sdlc-kit:prd`), feature design (`/sdlc-kit:spec`), or cross-feature
  technical requirements (`/sdlc-kit:trd`).
---

# sdlc-kit:adr

Creates and matures Architecture Decision Records under `02-architecture/adr/`.

---

## What an ADR is (and isn't)

| ADR is… | ADR isn't… |
|---|---|
| One architectural decision per file, append-only history | A place for open questions or TODOs (decide first, then write the ADR) |
| A MADR-shaped record: context, decision, alternatives, consequences | A runbook, design doc, or implementation plan |
| Numbered monotonically (`ADR-0001`, `ADR-0002`, …) and never renamed | A ticket — tickets track work, ADRs record reasoning |
| Linked from `00-steering/tech.md` (founding decisions) and from specs that depend on it | A description of every micro-choice; reserve ADRs for decisions that are *expensive to reverse* |

Statuses form a lifecycle: `proposed` → `accepted` → (optionally) `superseded` or `deprecated`. `rejected` terminates the lifecycle of a proposal that was considered and declined — it still stays on record.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:adr`, `/sdlc-kit:adr new <title>`, `/sdlc-kit:adr list`, `/sdlc-kit:adr accept <id>`, `/sdlc-kit:adr reject <id>`, `/sdlc-kit:adr supersede <old-id> --by <new-id>`, `/sdlc-kit:adr deprecate <id>`.
- The user says "record a decision", "write an ADR for X", "accept ADR 3", "deprecate that choice", "supersede the old DB decision", or equivalent phrasing in any other language.
- A discussion has converged on a choice that is expensive to reverse (framework, protocol, data model, deployment target, authz model, etc.) and no ADR captures it yet.

**Do not** invoke when:

- The decision is still being explored — finish the discussion first. An ADR records an outcome, not a debate.
- The user wants product requirements → `/sdlc-kit:prd`.
- The user wants feature-level requirements/design/tasks → `/sdlc-kit:spec`.
- The user wants cross-feature NFRs/SLIs/SLOs → `/sdlc-kit:trd`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/02-architecture/_templates/adr.md.tpl`. If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### List: `/sdlc-kit:adr` or `/sdlc-kit:adr list`

1. Run `adr.py --action list`. Parse the JSON `adrs` array.
2. Show a compact table: `id | status | title | updated`.
3. If empty, offer: "No ADRs yet. Want to record one with `/sdlc-kit:adr new <title>`?"
4. Otherwise, offer next actions: open any proposal, accept a mature draft, or create a new one.

### New ADR: `/sdlc-kit:adr new <title>`

1. **Derive the slug.** Propose a slug (lowercase ASCII, hyphen-separated) from the title and confirm — the user can override with `--slug`.
2. **List first** so you know the next number the script will assign.
3. **Scaffold.** Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-adr/scripts/adr.py" \
     --vault-root "<vault>" --action new \
     --title "<title>" [--slug "<slug>"] [--owner "<owner>"]
   ```
   The script picks the number (max existing + 1, 4-digit zero-padded), fills `{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`, and replaces the literal `ADR-NNNN` occurrences with the resolved id.
4. **Interview** (see below).

### The interview (LLM-driven, section by section)

Walk the template sections in this order, one focused question per section, editing in place via the Edit tool — do not rewrite the entire file at once.

1. **Context** — what forces are at play? What constraints, assumptions, and trade-offs motivate this decision? 2–4 paragraphs.
2. **Decision** — one sentence, imperative and concrete: "We adopt X for Y, with constraint Z." Then a short technical elaboration (components affected, interfaces changed).
3. **Alternatives considered** — at least one, ideally two. For each: pros, cons, reason for rejection. An ADR with no alternatives looks unexamined.
4. **Consequences** — positive, negative, and neutral. Negative consequences are accepted tech debt, not reasons to pick a different option.
5. **Implementation plan** — rough bullet list of follow-up steps (often links to epics/tasks).
6. **References** — wikilinks to `[[tech]]`, related ADRs, impacted specs.

Keep it to **≤6 questions**. Leave a placeholder when the user has nothing for a section and offer to revisit.

### Transition: `/sdlc-kit:adr {accept|reject|deprecate} <id>`

Map verb → target status:

| Verb | Target status | When to use |
|---|---|---|
| `accept` | `accepted` | Decision signed off and being implemented / in effect |
| `reject` | `rejected` | Proposal was considered and declined; record stays |
| `deprecate` | `deprecated` | Previously accepted, no longer applies, no direct replacement |

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-adr/scripts/adr.py" \
  --vault-root "<vault>" --action transition \
  --id "<id>" --to "<proposed|accepted|rejected|superseded|deprecated>"
```

`<id>` accepts `3`, `0003`, `ADR-3`, or `ADR-0003`.

Idempotent: if the ADR is already at the target status, the script writes nothing (keeps git clean).

### Supersede: `/sdlc-kit:adr supersede <old-id> --by <new-id>`

Superseding is a **two-file operation**. The script handles only status changes; the LLM handles the link edits.

1. Make sure the replacement ADR exists — if not, scaffold it first with `/sdlc-kit:adr new`.
2. Run `transition --id <old-id> --to superseded` via the script.
3. Edit both files via the Edit tool so the link is bidirectional:
   - In the old ADR's frontmatter: `superseded_by: "ADR-<new-id>"`
   - In the new ADR's frontmatter: `supersedes: ["ADR-<old-id>"]` (append, don't replace — a single ADR can supersede multiple predecessors).
   - In the body of both, add a paragraph under `## Status` explaining the relationship and the date.

### Sync

After every `new` or `transition` (including the supersede dance), invoke `/sdlc-kit:sync` so `_INDEX.md` and `02-architecture/_MOC.md` reflect the change.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "adrs": [
    {"id": "ADR-0001", "number": 1, "slug": "oauth-provider",
     "path": "02-architecture/adr/ADR-0001-oauth-provider.md",
     "title": "Use Auth0 as the IdP", "status": "accepted",
     "owner": "Milton", "updated": "2026-04-17"}
  ],
  "count": 1,
  "errors": []
}

// --action new
{
  "status": "ok",
  "action": "new",
  "vault_root": "/abs/path/.sdlc",
  "adr_id": "ADR-0003",
  "number": 3,
  "slug": "adopt-grpc-internal",
  "adr_path": "02-architecture/adr/ADR-0003-adopt-grpc-internal.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "adr_id": "ADR-0003",
  "adr_path": "02-architecture/adr/ADR-0003-adopt-grpc-internal.md",
  "previous_status": "proposed",
  "new_status": "accepted",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid id/slug/status, ADR not found, collision) · `2` fatal (permission denied, IO, missing template).

---

## Guardrails

**Never:**
- Renumber or rename an existing ADR. The ID is a stable reference — if the slug is wrong, accept it. If the decision is wrong, supersede it.
- Delete an ADR. Even rejected/superseded/deprecated ones stay on record.
- Auto-accept. `accepted` means humans signed off — always require explicit user approval.
- Fabricate alternatives. If the user only has one option to offer, ask what else was briefly considered and discarded. If truly nothing, leave the placeholder with a note.
- Rewrite the entire ADR in one Edit call — section-by-section only.

**Always:**
- Match the user's active conversation language.
- Run `--action list` before `new` so you can report the number the script will assign.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- For supersede: update both frontmatter blocks (`supersedes:` / `superseded_by:`) so the graph stays consistent.
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Recording a new decision:**
```
User: /sdlc-kit:adr new Adopt gRPC for internal services
AI:   [list] 2 existing ADRs; next will be ADR-0003.
AI:   Proposed slug: `adopt-grpc-internal`. OK?
User: ok
AI:   [new] created 02-architecture/adr/ADR-0003-adopt-grpc-internal.md (status=proposed)
AI:   "Let's fill this in. Starting with **Context** — what forces are at play?"
User: <answer>
AI:   [Edit tool: replace Context section]
AI:   "Next: **Decision**. In one sentence, what are we adopting and under what constraint?"
…
AI:   "All sections filled. Accept it now, or leave as `proposed` for review?"
User: leave as proposed; tech lead wants to review tomorrow
AI:   "Got it. When ready: `/sdlc-kit:adr accept 3`."
```

**Listing ADRs:**
```
User: /sdlc-kit:adr list
AI:   | id        | status    | title                          | updated    |
      |-----------|-----------|--------------------------------|------------|
      | ADR-0001  | accepted  | Use Auth0 as the IdP           | 2026-04-17 |
      | ADR-0002  | proposed  | Broken decision                | —          |
      | ADR-0003  | proposed  | Adopt gRPC for internal svcs   | 2026-04-17 |
AI:   "3 ADRs. Want to accept the gRPC one, or look at something else?"
```

**Accepting after review:**
```
User: /sdlc-kit:adr accept 3
AI:   [list] ADR-0003 — proposed.
AI:   "Confirm accepting ADR-0003 (Adopt gRPC for internal services)? Tech lead signed off?"
User: yes
AI:   [transition proposed→accepted] [/sdlc-kit:sync]
AI:   "✓ ADR-0003 is now accepted."
```

**Superseding an older decision:**
```
User: /sdlc-kit:adr supersede 1 by a new ADR about Keycloak
AI:   Step 1: scaffold the replacement ADR.
AI:   [new] created ADR-0004-migrate-to-keycloak.md (status=proposed)
AI:   [interview fills in context, decision referring back to ADR-0001, consequences…]
AI:   Step 2: mark ADR-0001 as superseded.
AI:   [transition ADR-0001 accepted→superseded]
AI:   Step 3: link both sides.
AI:   [Edit ADR-0001 frontmatter: superseded_by: "ADR-0004"]
AI:   [Edit ADR-0004 frontmatter: supersedes: ["ADR-0001"]]
AI:   [Edit ADR-0001 Status section: add a dated paragraph explaining the supersession]
AI:   [/sdlc-kit:sync]
AI:   "✓ ADR-0001 → superseded by ADR-0004. Both files linked."
```

**Idempotent transition:**
```
User: /sdlc-kit:adr accept 1
AI:   [list] ADR-0001 already accepted — nothing to do. Skipping sync.
```

---

## See also

- `scripts/adr.py` — file-op helper.
- `assets/vault-tree/02-architecture/_templates/adr.md.tpl` — canonical MADR template.
- `/sdlc-kit:steer tech` — product-wide technical principles that an ADR should align with.
- `/sdlc-kit:trd` — cross-feature technical requirements (NFRs, SLIs/SLOs).
- `/sdlc-kit:spec` — feature-level specs that may depend on an ADR.
- `/sdlc-kit:sync` — always invoked after ADR edits.
