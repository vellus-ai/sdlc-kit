---
type: ux-criteria
title: "UX Criteria — {{TITLE}}"
slug: "ux-criteria"
status: draft
phase: 06
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-ux
owner: "{{OWNER}}"
tags: [ux, research, product-design]
prd: "{{PRD_SLUG}}"
---

# UX Criteria — {{TITLE}}

> _(Gate 1 UX Research — defines who we're designing for, what they need, and what "done" looks like from a user perspective. Must be validated before Design System scaffold and TRD.)_

## 1. Personas

For each primary and secondary user type: name, role, context, goals, pain points.

### Persona 1: <Name>

- **Role / context:** <who they are and where they use the product>
- **Primary goal:** <what they want to accomplish>
- **Pain points:** <what frustrates them today>
- **Technical proficiency:** <low / medium / high>

<!-- Add more personas as needed -->

## 2. Jobs to be Done (JTBD)

*When* `<trigger>`, *I want to* `<action>`, *so I can* `<outcome>`.

| # | When | I want to | So I can |
|---|------|-----------|---------|
| JTBD-01 | | | |
| JTBD-02 | | | |

## 3. UX Acceptance Criteria

Testable, user-facing criteria — not implementation details. Each maps to one or more JTBDs.

| # | Criterion | JTBD | Priority |
|---|-----------|------|---------|
| UX-AC-01 | <GIVEN context / WHEN action / THEN observable outcome> | JTBD-01 | Must |
| UX-AC-02 | | | Should |

## 4. Accessibility Baseline (WCAG 2.1 AA)

- All user-facing surfaces comply with WCAG 2.1 Level AA (minimum).
- Additional surface-specific criteria: <list or N/A>
- Keyboard navigation: <required flows listed>
- Screen reader support: <required regions/announcements listed>

## 5. Content Guidelines

- Tone of voice: <formal / conversational / friendly>
- Error messages: <must be actionable, specific, non-technical>
- Empty states: <each major list / view must have a helpful empty state>
- Loading states: <skeleton / spinner / inline — specify per surface>

## 6. Anti-patterns (what we are NOT designing)

- <Pattern or feature explicitly out of scope for this initiative>

## 7. Open Questions

| # | Question | Owner | By |
|---|----------|-------|----|
| Q-01 | | | |

## References

- [[user-flows]] — user journey flows for this initiative
- [[_INDEX]] — global index
