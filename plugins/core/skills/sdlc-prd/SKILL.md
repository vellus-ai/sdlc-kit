---
name: sdlc-prd
description: |
  Use when the user wants to create, review, or transition a Product
  Requirements Document (PRD) — the top-level "what + for whom" doc for an
  initiative. Triggers: `/sdlc-kit:prd`, `/sdlc-kit:prd new <title>`,
  `/sdlc-kit:prd list`, `/sdlc-kit:prd promote <slug>`,
  `/sdlc-kit:prd archive <slug>`, "start a PRD for X",
  "define product requirements for Y", "register a new initiative",
  "ship the PRD", "archive this initiative". Mirror the user's chat
  language at runtime. Co-authored by a **Senior Engineer** (feasibility,
  testable KPIs, implementation risk) and an **Architect** (scope
  boundaries, cross-initiative dependencies, architectural implications).
  Each PRD lives at `01-planning/prd/<slug>.md`. Lifecycle:
  `draft → active → shipped → archived`. After scaffold or transition,
  invokes `/sdlc-kit:sync`. Do not invoke to record a technical decision
  (`/sdlc-kit:adr`), feature specs (`/sdlc-kit:spec`), or epics/milestones
  (`/sdlc-kit:epic`, `/sdlc-kit:milestone`).
---

# sdlc-kit:prd

Materializes and matures Product Requirements Documents under `01-planning/prd/`.

A PRD is **one initiative, one file** (`01-planning/prd/<slug>.md`), capturing
*what* and *for whom*, plus hypotheses, KPIs, scope boundaries. Linked to epics,
ADRs, and the product vision (`00-steering/product.md`). Signed off by the
product owner when it flips to `active`.

PRDs are **not** feature-level specs (`/sdlc-kit:spec`), architecture (no design
or contracts), or task lists (`/sdlc-kit:task`).

Lifecycle: `draft` → `active` → `shipped` → `archived`.

## When to invoke

Invoke when the user types `/sdlc-kit:prd [new|list|promote|archive] …`,
says "register a new initiative", "start a PRD for X", "ship the PRD",
"archive this initiative", or `/sdlc-kit:steer product` just finished and the
user wants the first concrete initiative.

**Do not** invoke for `/sdlc-kit:adr`, `/sdlc-kit:spec`, `/sdlc-kit:epic` /
`/sdlc-kit:milestone`, or when cwd is not inside a vault.

## Full flow

See `references/flow.md` for pre-checks, the 8-section interview, transitions
(promote/ship/archive/reopen), output contract, guardrails, and examples.
