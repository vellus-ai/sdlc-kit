---
name: sdlc-ux
description: |
  Use when the user wants to run Gate 1 of the frontend UX workflow — UX
  Research + Product Design — for a new initiative or feature with a
  user-facing surface. Creates or manages: `ux-criteria.md` (personas,
  JTBD, acceptance criteria), `user-flows.md` (user journeys), and
  `wireframes/<slug>.md` (lo-fi screen specs).
  Triggers: `/sdlc-kit:ux`, `/sdlc-kit:ux new <title>`,
  `/sdlc-kit:ux list`, `/sdlc-kit:ux wireframe <slug>`,
  `/sdlc-kit:ux approve`, `/sdlc-kit:ux deprecate`,
  "define UX for this feature", "create user flows",
  "scaffold a wireframe for <screen>", "document personas",
  "run UX research", "map the user journey".
  pt-BR: "definir UX", "criar user flows", "montar wireframe de <tela>",
  "documentar personas", "mapear jornada do usuário".
  Co-authored by a **UX Researcher** (personas, JTBD, behavioral insights)
  and a **Product Designer** (flows, information architecture, wireframes,
  WCAG 2.1 AA compliance). Artifacts live in `06-design-system/`:
  `ux-criteria.md` and `user-flows.md` are singletons; wireframes are
  a collection under `wireframes/<slug>.md`. Lifecycle: `draft` →
  `approved` → `deprecated`. Always invokes `/sdlc-kit:sync` after any
  write. Must be run before `/sdlc-kit:design-validation` (Gate 3).
  Do not invoke for architecture (`/sdlc-kit:c4`), feature specs
  (`/sdlc-kit:spec`), or domain modelling (`/sdlc-kit:domain`).
---

# sdlc-kit:ux

Gate 1 of the frontend UX workflow. Materializes UX research and product
design artifacts — the foundation that design system tokens and feature specs
are built on.

---

## Where UX artifacts fit in the vault

```
06-design-system/
├─ ux-criteria.md        — personas, JTBD, UX acceptance criteria (singleton)
├─ user-flows.md         — user journey flows mapped to JTBD (singleton)
├─ wireframes/
│   └─ <screen-slug>.md  — lo-fi screen spec (one per screen/modal)
├─ tokens/               — design tokens (sdlc-design-system)
├─ components/           — UI components (sdlc-design-system)
└─ patterns/             — interaction patterns (sdlc-design-system)
```

## Frontend UX Gate Sequence

```
Gate 1  /sdlc-kit:ux             ← this skill
Gate 2  /sdlc-kit:design-system  ← tokens, components, patterns
Gate 3  /sdlc-kit:design-validation  ← validates Gates 1+2 before TRD
Gate 4  /sdlc-kit:trd            ← technical requirements (NFRs)
```

The sequence is **advisory** — gates can run in parallel in experienced teams.
Gate 3 is a **hard gate** before TRD approval on any feature with UI surfaces.

---

## Lifecycle

| Status | Meaning |
|---|---|
| `draft` | Scaffolded, under research or review. Not safe to hand off to engineering. |
| `approved` | Product owner + design lead signed off. Engineering may plan against it. |
| `deprecated` | Replaced by a newer version or the initiative was cancelled. |

---

## When to invoke

- User types `/sdlc-kit:ux` or any form listed in the description triggers above.
- PRD just flipped to `active` and it has a frontend / UI scope — suggest this skill.
- A new screen, flow, or modal is being designed.

**Do not invoke when:**

- The feature has no user-facing surface (pure API / backend initiative).
- The user wants feature-level functional specs → `/sdlc-kit:spec`.
- The user wants architecture diagrams → `/sdlc-kit:c4`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** in `06-design-system/_templates/`. If missing, suggest
   `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg / list: `/sdlc-kit:ux` or `/sdlc-kit:ux list`

1. Run `ux.py --action list`. Parse the JSON `artifacts` array.
2. Show grouped summary:
   ```
   ux-criteria   — draft     (updated 2026-04-20)
   user-flows    — draft     (updated 2026-04-20)
   wireframes:
     login         — approved
     dashboard     — draft
   ```
3. Suggest next action:
   - If no artifacts → offer to scaffold with `/sdlc-kit:ux new <title>`.
   - If `draft` criteria/flows exist → suggest interview walkthrough.
   - If criteria + flows are approved → suggest running Gate 3:
     `/sdlc-kit:design-validation`.

### New: `/sdlc-kit:ux new <title>` (or natural language)

1. **Announce the triad**: "I'll co-author this as two lenses — **UX Researcher**
   (personas, JTBD, behavioral insights) and **Product Designer** (flows, IA,
   wireframes, accessibility)."
2. **Check PRD.** Ask which PRD slug this UX work belongs to (for traceability).
3. **List first** to detect collisions.
4. **Scaffold both singletons:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-ux/scripts/ux.py" \
     --vault-root "<vault>" --action scaffold \
     --kind ux-criteria --title "<title>" --prd-slug "<prd>"
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-ux/scripts/ux.py" \
     --vault-root "<vault>" --action scaffold \
     --kind user-flows --title "<title>" --prd-slug "<prd>"
   ```
5. **Run the UX Criteria interview** (Phase A).
6. **Run the User Flows interview** (Phase B).
7. Offer to scaffold wireframes for each identified screen.

### Wireframe: `/sdlc-kit:ux wireframe <slug>`

1. Confirm slug (kebab-case screen name, e.g. `login`, `checkout-step-2`).
2. Check that `ux-criteria.md` and `user-flows.md` exist — if not, warn and
   offer to scaffold them first.
3. Scaffold:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-ux/scripts/ux.py" \
     --vault-root "<vault>" --action scaffold \
     --kind wireframe --slug "<slug>" --title "<Title>"
   ```
4. Run the Wireframe interview (Phase C).
5. Invoke `/sdlc-kit:sync`.

### Approve / Deprecate: `/sdlc-kit:ux {approve|deprecate} [<slug>]`

| Verb | Applies to | Target status |
|---|---|---|
| `approve` | all singletons + all wireframes (or one if slug given) | `approved` |
| `deprecate` | same | `deprecated` |

For approve: run the pre-approval checklist first (see below).

```bash
python "...ux.py" --vault-root "<vault>" --action transition \
  --kind <kind> [--slug <slug>] --to <approved|deprecated>
```

---

## The interview (LLM-driven, triad, section by section)

Mirror the user's chat language. One focused question per section. Edit in
place — never rewrite the whole file in a single Edit call.

### Phase A — UX Criteria (`ux-criteria.md`)

Walk sections in order:

1. **Personas.** Who are the 1–3 primary users? Ask: role, context, goal,
   pain points, technical proficiency. Fill each `### Persona N` block.
2. **JTBD.** For each persona: "When `<trigger>`, I want to `<action>`, so I
   can `<outcome>`." Fill the JTBD table. At least 2–3 JTBDs required.
3. **UX Acceptance Criteria.** One criterion per JTBD. Format: GIVEN/WHEN/
   THEN at the user-observable level (not implementation). Must be testable
   without reading source code.
4. **Accessibility.** Confirm WCAG 2.1 AA baseline. Identify any surface-
   specific criteria (forms, navigation, modals, alerts).
5. **Content guidelines.** Tone, error message style, empty states, loading
   states.
6. **Anti-patterns.** What is explicitly NOT in scope.
7. **Open questions.** Any unresolved UX decisions — assign owner + deadline.

### Phase B — User Flows (`user-flows.md`)

Walk sections in order:

1. **Flow identification.** One flow per primary JTBD. Name each flow
   (e.g. "New User Registration", "Password Reset").
2. **Entry point.** Where does the user start? URL, notification, shared link?
3. **Happy path.** Step-by-step: "User `<action>` → System `<response>`".
   Keep each step atomic. At least 3 steps required.
4. **Error / edge paths.** For each decision point or system dependency:
   trigger, user message, system fallback.
5. **Exit points.** Success state + feedback. Any recovery mechanism for
   abandonment?
6. **Cross-flow diagram.** Offer to generate a Mermaid `flowchart TD` that
   wires all flows together. Fill the diagram block.

### Phase C — Wireframe (`wireframes/<slug>.md`)

Walk sections in order:

1. **Screen purpose.** Which flow + step does this screen serve?
2. **Layout regions.** ASCII sketch of the structural layout. Label each
   region (HEADER, SIDEBAR, CONTENT AREA, etc.). At minimum: 3 named regions.
3. **Content hierarchy.** Primary / secondary / tertiary content.
4. **Interactive elements.** Table of all actionable elements (buttons,
   inputs, links, toggles) with label + action + notes.
5. **Empty state.** What the user sees when no content is available.
6. **Error / feedback states.** Form errors, load failures, success messages.
7. **Responsive behavior.** Mobile / tablet / desktop layout changes.
8. **Accessibility notes.** Focus order, screen reader roles, touch targets.

---

## Pre-approval checklist

Block `approve` unless **all** apply:

- [ ] `ux-criteria.md`: ≥ 1 persona with all fields filled.
- [ ] `ux-criteria.md`: ≥ 2 JTBDs.
- [ ] `ux-criteria.md`: ≥ 1 UX acceptance criterion per JTBD.
- [ ] `ux-criteria.md`: Accessibility section filled (not placeholder).
- [ ] `user-flows.md`: ≥ 1 flow per JTBD with happy path + ≥ 1 edge path.
- [ ] `user-flows.md`: Cross-flow Mermaid diagram has no `<placeholder>` tokens.
- [ ] Wireframes: all primary screens identified in flows have a wireframe.
- [ ] No wireframe has an empty Layout Regions section.
- [ ] Product owner acknowledged the flows and criteria.

---

## Output contract

```json
// list
{ "status": "ok", "action": "list", "vault_root": "...", "kind": "",
  "artifacts": [{"kind": "ux-criteria", "slug": "ux-criteria", "path": "06-design-system/ux-criteria.md",
                 "title": "...", "status": "draft", "owner": "...", "updated": "..."}],
  "count": 1, "errors": [] }

// scaffold
{ "status": "ok", "action": "scaffold", "vault_root": "...",
  "kind": "ux-criteria", "slug": "ux-criteria",
  "artifact_path": "06-design-system/ux-criteria.md", "was_new": true, "errors": [] }

// transition
{ "status": "ok", "action": "transition", "vault_root": "...",
  "kind": "wireframe", "slug": "login",
  "artifact_path": "06-design-system/wireframes/login.md",
  "previous_status": "draft", "new_status": "approved", "errors": [] }
```

Exit codes: `0` ok/dry-run · `1` user error · `2` fatal.

---

## Guardrails

**Never:**
- Fabricate personas, JTBDs, or acceptance criteria — ask the user.
- Skip accessibility section — WCAG 2.1 AA is a hard requirement for every
  surface. Block `approve` if the accessibility section is a placeholder.
- Auto-approve — product owner must confirm explicitly.
- Skip error/edge paths in flows — a flow without edge paths is incomplete.
- Scaffold wireframes before `ux-criteria.md` exists — UX criteria gate
  the screen specs.

**Always:**
- Announce the UX Researcher + Product Designer triad before the interview.
- Mirror the user's active conversation language.
- Run `--action list` before scaffold to detect collisions.
- After each write, invoke `/sdlc-kit:sync`.
- After `approve`, suggest running Gate 3: `/sdlc-kit:design-validation`.

---

## Examples

**Full UX Gate 1 for a new initiative:**
```
User: /sdlc-kit:ux new Checkout v2
AI:   "Which PRD does this UX work belong to? (slug or N/A)"
User: checkout-v2
AI:   "I'll author this as two lenses — UX Researcher + Product Designer."
AI:   [scaffold ux-criteria + user-flows]
AI:   "Criteria scaffolded. Let's fill it in. **Personas** — describe the
       primary user: role, context, goal, pain points."
User: <answers>
AI:   [Edit: fill §1 Personas]
…
AI:   "Flows scaffolded. Flow 01 — what's the entry point for checkout?"
…
AI:   "Draft complete. Want to scaffold wireframes for each screen?
       Identified flows: Login, Cart Review, Payment, Confirmation."
User: yes, start with cart-review
AI:   [scaffold wireframe cart-review]
…
AI:   "Wireframe saved. When ready to validate: `/sdlc-kit:design-validation`."
```

**Listing UX artifacts:**
```
User: /sdlc-kit:ux list
AI:   ux-criteria   — draft
      user-flows    — draft
      wireframes:
        cart-review  — draft
      → Next: fill open sections, then `/sdlc-kit:ux approve`.
```

---

## See also

- `scripts/ux.py` — file-op helper.
- `06-design-system/_templates/{ux-criteria,user-flows,wireframe}.md.tpl`.
- `/sdlc-kit:design-validation` — Gate 3: validates UX + Design System before TRD.
- `/sdlc-kit:design-system` — Gate 2: design tokens, components, patterns.
- `/sdlc-kit:trd` — Gate 4: technical NFR requirements.
- `/sdlc-kit:spec` — feature specs that reference UX criteria wikilinks.
