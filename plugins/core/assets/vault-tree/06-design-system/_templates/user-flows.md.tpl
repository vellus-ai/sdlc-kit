---
type: user-flows
title: "User Flows — {{TITLE}}"
slug: "user-flows"
status: draft
phase: 06
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-ux
owner: "{{OWNER}}"
tags: [ux, user-flows, product-design]
prd: "{{PRD_SLUG}}"
---

# User Flows — {{TITLE}}

> _(Gate 1 UX Research — maps the user journey from entry point to outcome for each primary JTBD. Must be approved before wireframes are considered complete.)_

## Flow Structure

Each flow follows: **Trigger → Steps → Decision points → Outcomes**

Use the `Happy Path` + `Error / Edge Paths` separation for every flow.

---

## Flow 01: <Name — maps to JTBD-NN>

**Actor:** <Persona name>
**Entry point:** <Where does the user start? URL, notification, direct link, etc.>
**Goal:** <What the user wants at the end of this flow>

### Happy Path

```
1. User <action>
   → System <response>
2. User <action>
   → System <response>
   …
N. User reaches <outcome>
```

### Error / Edge Paths

| Trigger | User sees | System does |
|---------|-----------|-------------|
| <edge case> | <message or state> | <fallback> |

### Exit points

- **Success:** <state + feedback shown to user>
- **Abandonment:** <any save / recovery mechanism?>

---

<!-- Duplicate the Flow block for each primary JTBD -->

## Flow 02: <Name>

**Actor:**
**Entry point:**
**Goal:**

### Happy Path

```
1.
```

### Error / Edge Paths

| Trigger | User sees | System does |
|---------|-----------|-------------|
| | | |

---

## Cross-flow Diagram

```mermaid
flowchart TD
    A[Entry Point] --> B{Decision}
    B -->|Yes| C[Happy Path]
    B -->|No| D[Error Path]
    C --> E[Success State]
    D --> F[Recovery]
    F --> B
```

## References

- [[ux-criteria]] — acceptance criteria for this initiative
- [[_INDEX]] — global index
