---
type: design-component
title: "Component — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 06
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-design-system
owner: "{{OWNER}}"
tags: [design-system, component]
platform: ""
---

# Component — {{TITLE}}

> _(Component specification — purpose, API, variants, states, examples and accessibility.)_

## Purpose

In 1–2 paragraphs: what the component solves, in which context to use.

## When to use

- <appropriate scenario 1>
- <appropriate scenario 2>

## When NOT to use

- <inappropriate scenario 1 — point to alternative>
- <inappropriate scenario 2 — point to alternative>

## API / Props

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `variant` | `"primary" \| "secondary" \| "ghost"` | `"primary"` | no | visual style |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | no | size |
| `disabled` | `boolean` | `false` | no | disables interaction |
| `onClick` | `() => void` | — | yes | click handler |
| `children` | `ReactNode` | — | yes | text content |

## Variants

- **`primary`** — primary action on the screen.
- **`secondary`** — secondary or alternative action.
- **`ghost`** — tertiary action, no background.

## States

- **Default** — at rest.
- **Hover** — cursor over the component.
- **Focus** — keyboard focus (visible outline).
- **Active** — at click instant.
- **Disabled** — not interactive.
- **Loading** — action in progress.

## Consumed tokens

- [[<token-slug>]] — background
- [[<token-slug>]] — text color
- [[<token-slug>]] — radius

## Usage example

```tsx
<Button variant="primary" size="md" onClick={handleSubmit}>
  Save changes
</Button>
```

## Accessibility

- **Role:** `button` (or equivalent).
- **Keyboard:** `Enter` / `Space` triggers `onClick`.
- **Visible focus:** ≥ 2px outline with AA contrast.
- **ARIA:** `aria-label` mandatory when `children` is icon-only.
- **Contrast:** text over background ≥ 4.5:1.

## Related patterns

- [[<pattern-slug>]] — <pattern where this component is a piece>

## References

- [[_INDEX]] — global index
