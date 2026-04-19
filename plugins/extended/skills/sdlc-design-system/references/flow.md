# sdlc-kit:design-system — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/06-design-system/_templates/{token,component,pattern}.md.tpl`.

## Flow

### Zero-arg: `/sdlc-kit:design-system`

1. Run `design_system.py --action list` (no `--kind`).
2. Show grouped summary by kind:
   ```
   tokens:
     brand-primary    — stable
     spacing-base     — draft
   components:
     button           — stable
   patterns:
     modal            — deprecated (→ see [[dialog]])
   ```
3. Suggest next action (stabilize a draft, audit deprecated consumers, scaffold new).

### `new`: `/sdlc-kit:design-system new <kind> <slug>`

1. **Confirm kind and slug.** If user gave free text ("primary color"), propose `token` + `brand-primary` and confirm. The slug is the filename and wikilink key — hard to change later.
2. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-design-system/scripts/design_system.py" \
     --vault-root "<vault>" --action scaffold \
     --kind <token|component|pattern> \
     --slug <slug> --title "<Title>"
   ```
3. **Run the per-kind interview** (below), section by section.
4. Stay in `draft` until review; invoke `/sdlc-kit:sync`.

### Transitions

| Intent | Verb heard | Command |
|---|---|---|
| "stabilize" / "ready" / "approved" | stabilize | `--action transition --kind K --slug X --to stable` |
| "deprecate" / "retired" / "no longer use" | deprecate | `--action transition --kind K --slug X --to deprecated` |
| "reopen" / "back to draft" / "needs rework" | reopen | `--action transition --kind K --slug X --to draft` |

Transitions are **idempotent**.

Before `stable`, skim the entry and flag obvious gaps (token with empty `Base value`,
component with no documented states, pattern without interaction flow). Confirm before flipping.

Before `deprecated`, ask for a replacement; if there is one, insert wikilink at top:
"use [[<replacement>]] instead".

## The interview (LLM-driven, section by section)

Mirror the user's active conversation language. One focused question per section.

### Tokens (`--kind token`)

1. **Category** — color / typography / spacing / radius / shadow / motion / other. Tick the checkbox; refine `category:` frontmatter.
2. **Definition** — canonical name (`<namespace>.<category>.<variant>`), base value, unit, source. Base value must be **raw** (`#1E66F5`, `16px`, `4px`, `200ms`) — never a reference.
3. **Aliases** — semantic names mapping to this base. Real aliases only; don't invent.
4. **Usage** — wikilinks to consuming components. Pull from reality.
5. **Non-usage** — where this token should **not** be used (and why).
6. **Accessibility** — enforce **WCAG 2.1 AA** for color tokens:
   - **SC 1.4.3 Contrast (Minimum):** text ≥ 4.5:1; large text (≥ 18pt or ≥ 14pt bold) ≥ 3:1.
   - **SC 1.4.11 Non-text Contrast:** UI components, borders, icons, focus indicators ≥ 3:1.
   - **SC 1.4.1 Use of Color:** color must not be the **only** carrier — pair with icon/shape/text.
   - Dark-mode equivalent / inversion must carry the same ratios.
   - Target AAA when stated (SC 1.4.6: text 7:1, large 4.5:1) and mark accordingly.
7. **Technical export** — JSON snippet mirroring Definition.

### Components (`--kind component`)

1. **Purpose** — 1–2 paragraphs: what it solves, when to reach for it.
2. **When to use / When NOT to use** — 1–3 bullets each. "When NOT" should point to an alternative.
3. **API / Props** — complete the table; mark `Required` honestly.
4. **Variants** — name them (`primary`, `secondary`, `ghost`…) and describe intent.
5. **States** — default / hover / focus / active / disabled / loading. Remove rows that don't apply.
6. **Consumed tokens** — wikilinks to the design tokens. Tokens must already exist.
7. **Usage example** — one complete, copy-pasteable code example.
8. **Accessibility** — enforce **WCAG 2.1 AA**:
   - **SC 4.1.2 Name, Role, Value:** correct role; name and state exposed to AT.
   - **SC 2.1.1 Keyboard:** fully reachable; document key bindings (Enter/Space/Arrow/Esc/Tab).
   - **SC 2.4.7 Focus Visible** + **SC 1.4.11 Non-text Contrast:** focus ≥ 3:1, perceivable without color alone.
   - **SC 1.4.3 Contrast (Minimum):** text vs background ≥ 4.5:1 (large ≥ 3:1) across every variant × state × theme.
   - **SC 1.4.4 / 1.4.10:** works at 200% zoom and 320 CSS px.
   - **SC 2.5.5 / 2.5.8:** target ≥ 24×24 px (preferably 44×44).
   - **SC 1.3.1 Info and Relationships:** labels, errors, descriptions programmatically associated.
   - For form components add **SC 3.3.1 / 3.3.2 / 3.3.3** — error identification, labels, suggestion.
9. **Related patterns** — patterns that consume this component.

### Patterns (`--kind pattern`)

1. **Problem** — interaction problem solved (1 paragraph).
2. **When to use** — 1–3 scenarios.
3. **Anti-pattern** — what looks like a solution but isn't, with rationale and alternative.
4. **Structure** — ASCII/unicode box sketch.
5. **Involved components** — wikilinks + role.
6. **Interaction flow** — numbered user/system steps.
7. **Variations** — named variations with when/why.
8. **Accessibility** — enforce **WCAG 2.1 AA** at the flow level:
   - **SC 2.4.3 Focus Order:** initial focus and tab order logical, follow reading order.
   - **SC 2.1.2 No Keyboard Trap:** dismissable by keyboard alone (Esc / explicit close).
   - **SC 4.1.3 Status Messages:** live-region announcements (`role="status"`, `role="alert"`, `aria-live`).
   - **SC 2.4.11 Focus Not Obscured (2.2):** focused element not hidden by overlays/sticky headers.
   - **SC 2.2.1 / 2.2.2:** for timeouts/auto-advance/motion expose controls and respect `prefers-reduced-motion`.
   - **SC 1.3.2 Meaningful Sequence:** DOM order mirrors visual flow.
   - For modal/dialog: focus trap + restoration to trigger on close.
9. **Production examples** — real screens/flows where the pattern lives.

## Output contract

```json
// --action list (optionally --kind K)
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "kind": "",
  "entries": [
    {"kind": "token", "slug": "brand-primary",
     "path": "06-design-system/tokens/brand-primary.md",
     "title": "Token — Brand Primary", "status": "stable",
     "owner": "Milton", "updated": "2026-04-10"}
  ],
  "count": 1,
  "errors": []
}

// --action scaffold --kind K --slug X --title T
{
  "status": "ok", "action": "scaffold",
  "kind": "component", "slug": "button",
  "entry_path": "06-design-system/components/button.md",
  "was_new": true, "errors": []
}

// --action transition --kind K --slug X --to S
{
  "status": "ok", "action": "transition",
  "kind": "token", "slug": "brand-primary",
  "entry_path": "06-design-system/tokens/brand-primary.md",
  "previous_status": "draft", "new_status": "stable",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Overwrite an existing entry without `--force` and explicit confirmation.
- Rewrite the entry body in a single Edit call — section-by-section only.
- Fabricate token values. Raw values only — never guess `"some-brand-color"`; ask or leave `<tbd>`.
- Fabricate aliases or consumers. Real names only.
- Auto-promote to `stable` or `deprecated`.
- Auto-derive accessibility claims or ship a spec that does not comply with **WCAG 2.1 AA**:
  - Text contrast (SC 1.4.3): ≥ 4.5:1 normal, ≥ 3:1 large.
  - Non-text contrast (SC 1.4.11): ≥ 3:1.
  - Color alone (SC 1.4.1): never the sole carrier.
  - Keyboard (SC 2.1.1 / 2.1.2): fully operable, no trap.
  - Focus visible (SC 2.4.7).
  - Name/Role/Value (SC 4.1.2) and Status messages (SC 4.1.3).
  - Resize/Reflow (SC 1.4.4 / 1.4.10): usable at 200% zoom and 320 CSS px.
  - Target size: SC 2.5.8 (≥ 24×24 px, 44×44 when feasible).
  If unconfirmed, leave `<!-- TODO WCAG 2.1 AA: <criterion> -->` and keep `draft`.
- Promote to `stable` while any WCAG 2.1 AA criterion is unmet — hard stop.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md`.

**Always:**
- Mirror user's chat language.
- Run `--action list` before scaffold/transition.
- Confirm kind + slug with the user before scaffolding.
- Before promoting to `stable`, run a **WCAG 2.1 AA compliance pass** and surface checklist results:
  - Tokens: SC 1.4.1, 1.4.3, 1.4.11.
  - Components: SC 1.3.1, 1.4.3, 1.4.4, 1.4.10, 1.4.11, 2.1.1, 2.4.7, 2.5.8, 4.1.2, 4.1.3 (+ 3.3.1/3.3.2/3.3.3 for form inputs).
  - Patterns: SC 1.3.2, 2.1.2, 2.2.1, 2.2.2, 2.4.3, 2.4.11, 4.1.3.
  Block the transition and keep `draft` if any criterion is unmet.
- For tokens consumed by a component, ensure token entries exist first.
- On `deprecated`, ask for the replacement wikilink and insert it at the top.
- Invoke `/sdlc-kit:sync` after scaffold or transition.

## Examples

> Mirror the user's active conversation language in every user-facing line.

**Fresh color token:**
```
User: /sdlc-kit:design-system new token brand-primary
AI:   "Kind: `token`, slug: `brand-primary`. Confirm?"
User: yes
AI:   [scaffold --kind token --slug brand-primary --title "Brand Primary"]
AI:   "Let's fill this in. **Category** — color, spacing, typography…?"
User: color
AI:   [Edit: tick `[x] Color (color)` and frontmatter `category: color`]
AI:   "**Definition** — canonical name, base value, unit, source?"
User: brand.color.primary.500 = #1E66F5, source: brand guideline v3
…
```

**Stabilizing a component:**
```
User: o Button está aprovado, pode marcar como stable
AI:   "Dei uma olhada em `components/button.md`:
       - API/Props ✓ - States 6/6 ✓ - Tokens 4 wikilinks válidos ✓
       - Accessibility: role, keyboard, contrast — ok ✓
       Pronto para `stable`. Confirma?"
User: confirma
AI:   [transition --kind component --slug button --to stable] [/sdlc-kit:sync]
```

**Deprecating a pattern with replacement:**
```
User: o pattern `modal` foi substituído pelo `dialog`
AI:   [transition --kind pattern --slug modal --to deprecated]
AI:   [Edit: insert `> **Deprecated** — use [[dialog]] instead.` at top of body]
AI:   [/sdlc-kit:sync]
```

**Listing one kind:**
```
User: /sdlc-kit:design-system list tokens
AI:   brand-primary    — stable
      spacing-base     — draft
      legacy-accent    — deprecated (→ [[brand-primary]])
```

## See also

- `scripts/design_system.py` — file-op helper.
- `assets/vault-tree/06-design-system/_templates/{token,component,pattern}.md.tpl`.
- `/sdlc-kit:c4` — architecture diagrams.
- `/sdlc-kit:spec` — feature specs that consume design-system entries.
- `/sdlc-kit:sync` — always invoked after design-system edits.
