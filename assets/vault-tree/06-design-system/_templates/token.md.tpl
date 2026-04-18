---
type: design-token
title: "Token — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 06
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-design-system
owner: "{{OWNER}}"
tags: [design-system, token]
category: ""
---

# Token — {{TITLE}}

> _(Design system token — atomic value reused by components.)_

## Category

- [ ] Color (color)
- [ ] Typography (typography)
- [ ] Spacing
- [ ] Radius
- [ ] Shadow
- [ ] Motion (duration / easing)
- [ ] Other: <specify>

## Definition

- **Canonical name:** `<namespace>.<category>.<variant>` (ex: `brand.color.primary.500`).
- **Base value:** `<value>` (ex: `#1E66F5`, `16px`, `600`, `4px`).
- **Unit:** `<px / rem / ms / unitless>`.
- **Source:** <where it came from — brand guideline, design spec>.

## Aliases

Named tokens that point to this base token.

- `semantic.color.action.primary` → `brand.color.primary.500`
- `semantic.color.action.primary.hover` → `brand.color.primary.600`

## Usage

In which components and contexts this token is applied.

- [[<component-slug>]] — background of `default` state.
- [[<component-slug>]] — text over dark surface.

## Non-usage

Where this token should **not** be applied and why.

- Don't use as text color on white background (insufficient AA contrast).
- Don't use in error states (reserved for `semantic.color.feedback.error`).

## Accessibility

- **Contrast (when applicable):** AA ≥ 4.5:1 for normal text, 3:1 for large text or UI components.
- **Dark mode:** <equivalent token or inversion rule>.

## Technical export

```json
{
  "brand.color.primary.500": {
    "value": "#1E66F5",
    "type": "color",
    "description": "Primary brand color, medium intensity."
  }
}
```

## References

- [[<component-slug>]] — consuming component
- [[_INDEX]] — global index
