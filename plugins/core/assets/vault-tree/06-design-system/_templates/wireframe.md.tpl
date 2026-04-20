---
type: wireframe
title: "Wireframe — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 06
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-ux
owner: "{{OWNER}}"
tags: [ux, wireframe, product-design]
screen: "{{SLUG}}"
flow: ""
---

# Wireframe — {{TITLE}}

> _(Lo-fi structural spec for a screen or modal. Describes layout regions, content hierarchy, and interactive elements — not visual polish. Must reference the user flow it belongs to.)_

## Screen Purpose

1–2 sentences: what user task this screen accomplishes and which flow it belongs to.

- **Flow:** [[user-flows]] → Flow NN: <Flow name>
- **Route / URL:** `<route or N/A>`
- **Entry points:** <links or navigation items that lead here>

## Layout Regions

Use ASCII/unicode to sketch the structural layout. Label each region.

```
┌─────────────────────────────────────┐
│  HEADER                             │
│  [Logo]            [Nav] [CTA Btn]  │
├─────────────────────────────────────┤
│  PAGE TITLE                         │
│  <H1> + <subtitle>                  │
├──────────────────┬──────────────────┤
│  SIDEBAR / FILTER│  CONTENT AREA    │
│  [ ]  Filter A   │  Card 1          │
│  [ ]  Filter B   │  Card 2          │
│                  │  ...             │
└──────────────────┴──────────────────┘
│  FOOTER                             │
└─────────────────────────────────────┘
```

## Content Hierarchy

1. **Primary content:** <what the user focuses on first>
2. **Secondary content:** <supporting information>
3. **Tertiary / utility:** <navigation, metadata, actions>

## Interactive Elements

| Element | Type | Label | Action | Notes |
|---------|------|-------|--------|-------|
| CTA Button | Button (primary) | <label> | <navigates to / submits / opens modal> | |
| Filter A | Checkbox | <label> | <filters list> | Multi-select |
| Form field | Input text | <placeholder> | <validates on blur> | Required |

## Empty State

What the user sees when there is no content to display.

- **Illustration:** <icon / image placeholder>
- **Headline:** `<message>`
- **CTA:** `<action label>` → `<action>`

## Error / Feedback States

| State | Trigger | What user sees |
|-------|---------|---------------|
| Form error | Submit with missing required field | Inline error below field |
| Load failure | API error | Toast: "Could not load data. Try again." |
| Success | Form submitted | Toast: "Saved successfully." |

## Responsive Behavior

- **Mobile (< 640px):** <describe layout change, e.g. sidebar collapses to accordion>
- **Tablet (640–1024px):** <changes if any>
- **Desktop (≥ 1024px):** <as sketched above>

## Accessibility Notes

- Focus order: <describe expected tab order through interactive elements>
- Screen reader: <heading structure, landmark roles, live-region needs>
- Touch targets: all tappable elements ≥ 44 × 44 px

## Related

- [[user-flows]] — flow this screen is part of
- [[ux-criteria]] — acceptance criteria this screen must satisfy
- [[_INDEX]] — global index
