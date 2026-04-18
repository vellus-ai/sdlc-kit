---
name: sdlc-design-system
description: |
  Use when the user wants to create, list, or change the status of a
  design-system entry — a design token (atomic value), a component (reusable
  UI spec) or a pattern (recurring combination of components). English
  triggers: `/sdlc-kit:design-system`,
  `/sdlc-kit:design-system new token <slug>`,
  `/sdlc-kit:design-system new component <slug>`,
  `/sdlc-kit:design-system new pattern <slug>`,
  `/sdlc-kit:design-system list`,
  `/sdlc-kit:design-system {stabilize|deprecate|reopen} <kind> <slug>`,
  "create a primary-color token", "document the Button component",
  "the Card pattern is stable now", "deprecate the legacy-input token".
  pt-BR triggers: "criar um token de cor primária",
  "documentar o componente Button", "o padrão Card está estável",
  "deprecar o token legacy-input", "marcar o modal como draft de novo".
  Driven by a **Design System Lead** persona — owns the visual/interaction
  vocabulary, WCAG 2.1 AA compliance, and the token → component → pattern
  inheritance chain. Creates one file per entry under
  `06-design-system/{tokens,components,patterns}/<slug>.md` from the
  corresponding template. The script handles deterministic operations
  (list / scaffold / transition); the LLM drives the per-kind interview
  (category/base value/aliases for tokens, API/variants/states/accessibility
  for components, structure/flow/anti-patterns for patterns) section-by-section
  via Edit, mirroring the user's chat language. Lifecycle: `draft` → `stable`
  → `deprecated`, reversible to `draft` via `reopen`. Always invokes
  `/sdlc-kit:sync` after any change. Do not invoke for architecture docs
  (`/sdlc-kit:c4`), feature specs (`/sdlc-kit:spec`), or domain modelling
  (`/sdlc-kit:domain`).
---

# sdlc-kit:design-system

Materializes and matures design-system entries — the visual and interaction
vocabulary the product is built from.

---

## Where design-system entries fit

```
06-design-system/
├─ tokens/       — atomic values (colors, spacing, typography, radii, motion)
├─ components/   — reusable UI specs (API, variants, states, accessibility)
└─ patterns/     — recurring combinations of components solving an interaction
                  problem (e.g. Dialog, Wizard, Empty-state)
```

Tokens feed components; components feed patterns. All three live side by side
but each has its own template and its own interview focus.

One file per entry. Templates are copied from `06-design-system/_templates/`
into `06-design-system/{tokens,components,patterns}/<slug>.md` at scaffold
time.

---

## Lifecycle

| Status | Meaning |
|---|---|
| `draft` | Scaffolded, being defined or reviewed. Not safe to consume. |
| `stable` | Reviewed and approved — free to consume in product work. |
| `deprecated` | Kept for history; do not adopt in new work. Point to the replacement. |

Start in `draft`. Promote to `stable` only after explicit review (design and
engineering). Flip to `deprecated` when a replacement exists or the entry is
no longer supported. `reopen` is reachable from `stable`/`deprecated` back to
`draft` when the spec needs rework.

Status progression is a **qualitative** call the user makes — the script never
promotes automatically.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:design-system`, `/sdlc-kit:design-system new <kind> <slug>`,
  `/sdlc-kit:design-system list [<kind>]`, `/sdlc-kit:design-system {stabilize|deprecate|reopen} <kind> <slug>`.
- The user says "create a token for primary color", "document the Button
  component", "the Wizard pattern is stable now", "deprecate the legacy-input
  token" — or equivalent phrasing in any other language.
- A new visual constant, UI component, or interaction pattern needs a
  canonical spec in the vault.

**Do not** invoke when:

- The user wants a feature-level spec → use `/sdlc-kit:spec`.
- The user wants architecture diagrams → use `/sdlc-kit:c4`.
- The user wants domain modelling → use `/sdlc-kit:domain`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/06-design-system/_templates/{token,component,pattern}.md.tpl`.
   If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg: `/sdlc-kit:design-system`

1. Run `design_system.py --action list` (no `--kind`). Parse the JSON `entries`
   array.
2. Show the user a grouped summary — one line per entry, grouped by kind:
   ```
   tokens:
     brand-primary    — stable
     spacing-base     — draft
   components:
     button           — stable
     card             — draft
   patterns:
     modal            — deprecated (→ see [[dialog]])
   ```
3. Suggest next action:
   - If any `draft` entry is old or incomplete → "Want to stabilize `<slug>`?"
   - If a deprecated entry still has live consumers → "Want to audit who
     still uses `<slug>`?"
   - Else → "Want to scaffold a new token / component / pattern?"

### `new`: `/sdlc-kit:design-system new <kind> <slug>` (or natural language)

1. **Confirm kind and slug.** If the user gave free text (e.g. "primary
   color"), propose a kind (`token`) and slug (`brand-primary`) and confirm
   before scaffolding. The slug is the filename and wikilink key — hard to
   change later.
2. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-design-system/scripts/design_system.py" \
     --vault-root "<vault>" --action scaffold \
     --kind <token|component|pattern> \
     --slug <slug> --title "<Title>"
   ```
3. **Run the interview** (see the per-kind sections below), section by section.
4. When the user is happy with the initial draft (it stays `draft` until
   review), invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb heard | Command |
|---|---|---|
| "stabilize" / "ready" / "approved" | stabilize | `--action transition --kind K --slug X --to stable` |
| "deprecate" / "retired" / "no longer use" | deprecate | `--action transition --kind K --slug X --to deprecated` |
| "reopen" / "back to draft" / "needs rework" | reopen | `--action transition --kind K --slug X --to draft` |

Transitions are **idempotent** — re-running with the current status writes
nothing.

Before marking `stable`, the LLM should skim the entry and flag obvious gaps:
a token with an empty `Base value`, a component with no documented states, a
pattern without an interaction flow. Ask the user to confirm before flipping.

Before marking `deprecated`, ask whether there is a replacement entry and, if
so, offer to insert a wikilink at the top of the body — "use [[<replacement>]]
instead".

---

## The interview (LLM-driven, section by section)

Mirror the user's active conversation language. One focused question per
section. Do not rewrite the file in a single Edit — always section-by-section.

### Tokens (`--kind token`)

Walk the template in order:

1. **Category** — which of color / typography / spacing / radius / shadow /
   motion / other. Tick the checkbox; offer to refine the `category:`
   frontmatter field to the chosen value (e.g. `color`, `spacing`).
2. **Definition** — canonical name (`<namespace>.<category>.<variant>`),
   base value, unit, source. The base value must be a **raw** value
   (`#1E66F5`, `16px`, `4px`, `200ms`) — not a reference to another token.
3. **Aliases** — semantic names that map to this base token, if any. Real
   aliases only; don't invent them.
4. **Usage** — wikilinks to components that consume this token. Pull from
   reality — don't invent consumers.
5. **Non-usage** — where this token should **not** be used (and why).
6. **Accessibility** — enforce **WCAG 2.1 AA** for color tokens:
   - **SC 1.4.3 Contrast (Minimum):** text ≥ 4.5:1; large text (≥ 18pt, or
     ≥ 14pt bold) ≥ 3:1.
   - **SC 1.4.11 Non-text Contrast:** UI components and graphical objects
     (borders, icons, focus indicators, input boundaries) ≥ 3:1 against
     adjacent colors.
   - **SC 1.4.1 Use of Color:** color must not be the **only** visual means
     of conveying information — pair with icon/shape/text.
   - Dark-mode equivalent or inversion rule must carry the same ratios.
   - Target AAA when stated by the product (SC 1.4.6: text 7:1, large 4.5:1)
     and mark the token accordingly.
7. **Technical export** — JSON snippet mirroring Definition.

### Components (`--kind component`)

Walk the template in order:

1. **Purpose** — 1–2 paragraphs: what it solves, when to reach for it.
2. **When to use / When NOT to use** — list 1–3 bullets each. "When NOT to
   use" should point to an alternative (component or pattern).
3. **API / Props** — complete the table; mark `Required` honestly.
4. **Variants** — name them (`primary`, `secondary`, `ghost`…) and describe
   intent.
5. **States** — default / hover / focus / active / disabled / loading. Keep
   only the states the component actually has; remove rows that don't apply.
6. **Consumed tokens** — wikilinks to the design tokens the component reads.
   Tokens must already exist in `tokens/` (scaffold them first if not).
7. **Usage example** — one complete, copy-pasteable code example.
8. **Accessibility** — enforce **WCAG 2.1 AA**. Every component entry must
   confirm, at minimum:
   - **SC 4.1.2 Name, Role, Value:** correct native role or ARIA role; name
     and state exposed to assistive tech.
   - **SC 2.1.1 Keyboard:** all functionality reachable via keyboard; document
     the key bindings (Enter/Space/Arrow/Esc/Tab).
   - **SC 2.4.7 Focus Visible** + **SC 1.4.11 Non-text Contrast:** focus
     indicator visible against its background at ≥ 3:1 and perceivable
     without color alone.
   - **SC 1.4.3 Contrast (Minimum):** text vs. background ≥ 4.5:1 (large
     text ≥ 3:1); verify across every variant × state × theme the component
     supports.
   - **SC 1.4.4 Resize Text / 1.4.10 Reflow:** component keeps working at
     200 % zoom and 320 CSS px width.
   - **SC 2.5.5 Target Size (AAA) / 2.5.8 Target Size (AA, 2.2 — adopt
     preemptively):** interactive target ≥ 24 × 24 px (preferably 44 × 44).
   - **SC 1.3.1 Info and Relationships:** labels, error messages and
     descriptions programmatically associated (`aria-labelledby`,
     `aria-describedby`, etc.).
   - For form components add **SC 3.3.1 / 3.3.2 / 3.3.3** — error
     identification, labels/instructions, error suggestion.
9. **Related patterns** — patterns that consume this component.

### Patterns (`--kind pattern`)

Walk the template in order:

1. **Problem** — the interaction problem being solved (1 paragraph).
2. **When to use** — 1–3 scenarios.
3. **Anti-pattern** — what looks like a solution but is not, with rationale
   and alternative.
4. **Structure** — ASCII/unicode box sketch of the pattern anatomy.
5. **Involved components** — wikilinks to the components that participate
   and their role.
6. **Interaction flow** — numbered user/system steps.
7. **Variations** — named variations with when/why to use each.
8. **Accessibility** — enforce **WCAG 2.1 AA** at the flow level:
   - **SC 2.4.3 Focus Order:** initial focus and tab order are logical and
     follow reading order; document both.
   - **SC 2.1.2 No Keyboard Trap:** the pattern must be dismissable by
     keyboard alone (Esc / explicit close); document the exit key(s).
   - **SC 4.1.3 Status Messages:** live-region announcements for dynamic
     state (opened / closed / loading / error). Specify `role="status"`,
     `role="alert"`, or `aria-live` policy.
   - **SC 2.4.11 Focus Not Obscured (2.2 — adopt preemptively):** the
     focused element must not be hidden by overlays, sticky headers or the
     pattern itself.
   - **SC 2.2.1 Timing Adjustable / 2.2.2 Pause, Stop, Hide:** for
     patterns with timeouts, auto-advance or motion, expose controls and
     respect `prefers-reduced-motion`.
   - **SC 1.3.2 Meaningful Sequence:** DOM order mirrors the visual flow so
     the pattern reads the same with CSS disabled.
   - For modal/dialog-like patterns add focus trap + restoration to the
     trigger on close (classic dialog contract).
9. **Production examples** — real screens/flows where the pattern lives.

---

## Output contract

```json
// --action list (optionally --kind K)
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "kind": "",
  "entries": [
    {
      "kind": "token",
      "slug": "brand-primary",
      "path": "06-design-system/tokens/brand-primary.md",
      "title": "Token — Brand Primary",
      "status": "stable",
      "owner": "Milton",
      "updated": "2026-04-10"
    }
  ],
  "count": 1,
  "errors": []
}

// --action scaffold --kind K --slug X --title T
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "kind": "component",
  "slug": "button",
  "entry_path": "06-design-system/components/button.md",
  "was_new": true,
  "errors": []
}

// --action transition --kind K --slug X --to S
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "kind": "token",
  "slug": "brand-primary",
  "entry_path": "06-design-system/tokens/brand-primary.md",
  "previous_status": "draft",
  "new_status": "stable",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (missing arg, invalid kind,
invalid slug, already exists, not found, invalid status) · `2` fatal
(permission denied, IO, template missing).

---

## Guardrails

**Never:**
- Overwrite an existing entry file without `--force` and explicit user
  confirmation.
- Rewrite the entry body in a single Edit call — always section-by-section.
- Fabricate token values. Raw values only (`#1E66F5`, `16px`) — never guess
  `"some-brand-color"` or similar placeholders; ask the user or leave the
  field marked `<tbd>`.
- Fabricate aliases or consumers. Only list semantic names and component
  references that actually exist.
- Auto-promote to `stable` or `deprecated` — always require explicit user
  approval; flag gaps (missing value, undocumented states, no interaction
  flow) before flipping.
- Auto-derive accessibility claims or ship a spec that does not comply with
  **WCAG 2.1 Level AA** (baseline for every entry). Minimums — non-negotiable:
  - **Text contrast (SC 1.4.3):** ≥ 4.5:1 normal, ≥ 3:1 large (≥ 18pt or
    ≥ 14pt bold).
  - **Non-text contrast (SC 1.4.11):** ≥ 3:1 for UI components, state
    boundaries, focus indicators and meaningful graphical objects.
  - **Color alone (SC 1.4.1):** never the sole carrier of information — pair
    with text, icon or shape.
  - **Keyboard (SC 2.1.1 / 2.1.2):** fully operable by keyboard, no trap.
  - **Focus visible (SC 2.4.7):** visible indicator in every interactive
    state.
  - **Name/Role/Value (SC 4.1.2) and Status messages (SC 4.1.3):** exposed
    to assistive tech.
  - **Resize/Reflow (SC 1.4.4 / 1.4.10):** content usable at 200 % zoom and
    320 CSS px viewport.
  - **Target size:** adopt WCAG 2.2 SC 2.5.8 (≥ 24 × 24 px, 44 × 44 when
    feasible).
  If the user cannot confirm any of the above, leave the section with an
  explicit `<!-- TODO WCAG 2.1 AA: <criterion> -->` marker and keep the
  entry in `draft` — **never** promote to `stable`.
- Promote an entry to `stable` while any WCAG 2.1 AA criterion is unmet
  or marked as TODO — this is a hard stop, regardless of user urgency.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md` — those are managed by
  `/sdlc-kit:sync` and the user.

**Always:**
- Mirror the user's active conversation language.
- Run `--action list` before scaffold/transition so you know the current
  state.
- Confirm the kind (`token` / `component` / `pattern`) and slug with the
  user before scaffolding.
- Before promoting any entry to `stable`, run a **WCAG 2.1 AA compliance
  pass** against the relevant success criteria and surface the checklist
  results to the user for explicit confirmation:
  - Tokens: SC 1.4.1, 1.4.3, 1.4.11.
  - Components: SC 1.3.1, 1.4.3, 1.4.4, 1.4.10, 1.4.11, 2.1.1, 2.4.7,
    2.5.8 (WCAG 2.2), 4.1.2, 4.1.3 (+ 3.3.1/3.3.2/3.3.3 for form inputs).
  - Patterns: SC 1.3.2, 2.1.2, 2.2.1, 2.2.2, 2.4.3, 2.4.11 (WCAG 2.2),
    4.1.3.
  Block the transition and keep `status: draft` if any criterion is unmet
  or unconfirmed.
- For tokens consumed by a component, ensure the token entries already exist
  — scaffold them first if not.
- On `deprecated`, ask for the replacement wikilink and insert it at the top
  of the body.
- Invoke `/sdlc-kit:sync` after scaffold or transition.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active
> conversation language in every user-facing line.

**Fresh color token:**
```
User: /sdlc-kit:design-system new token brand-primary
AI:   "Kind: `token`, slug: `brand-primary`. Confirm?"
User: yes
AI:   [scaffold --kind token --slug brand-primary --title "Brand Primary"]
AI:   [scaffold] created 06-design-system/tokens/brand-primary.md.
AI:   "Let's fill this in. **Category** — color, spacing, typography…?"
User: color
AI:   [Edit: tick `[x] Color (color)` and set frontmatter `category: color`]
AI:   "**Definition** — canonical name, base value, unit, source?"
User: brand.color.primary.500 = #1E66F5, source: brand guideline v3
AI:   [Edit the Definition bullets]
…
AI:   "Draft saved, staying in `draft` until design review. Want me to
       `/sdlc-kit:sync` now?"
```

**Stabilizing a component:**
```
User: o Button está aprovado, pode marcar como stable
AI:   "Dei uma olhada em `components/button.md`:
       - API / Props: preenchido ✓
       - States: 6/6 documentados ✓
       - Consumed tokens: 4 wikilinks válidos ✓
       - Accessibility: role, keyboard, contrast — ok ✓
       Pronto para `stable`. Confirma?"
User: confirma
AI:   [transition --kind component --slug button --to stable]
AI:   [/sdlc-kit:sync]
```

**Deprecating a pattern with replacement:**
```
User: o pattern `modal` foi substituído pelo `dialog`; pode deprecar
AI:   [transition --kind pattern --slug modal --to deprecated]
AI:   [Edit: insert `> **Deprecated** — use [[dialog]] instead.` at the top
             of the body, below the title]
AI:   [/sdlc-kit:sync]
AI:   "✓ `modal` marcado como deprecated e apontando para `[[dialog]]`."
```

**Listing one kind:**
```
User: /sdlc-kit:design-system list tokens
AI:   brand-primary    — stable
      brand-secondary  — stable
      spacing-base     — draft
      legacy-accent    — deprecated (→ [[brand-primary]])
AI:   "Want to stabilize `spacing-base` or audit who still uses
       `legacy-accent`?"
```

---

## See also

- `scripts/design_system.py` — file-op helper.
- `assets/vault-tree/06-design-system/_templates/{token,component,pattern}.md.tpl` — canonical templates (copied into each vault at init time).
- `/sdlc-kit:c4` — architecture diagrams; pair with components when they map to containers.
- `/sdlc-kit:spec` — feature specs that consume design-system entries.
- `/sdlc-kit:sync` — always invoked after design-system edits.
