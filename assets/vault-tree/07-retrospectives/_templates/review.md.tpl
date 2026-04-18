---
type: review
title: "{{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 07
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-review
owner: "{{OWNER}}"
tags: [retrospective, review, pr, appsec]
pr: ""
pr_url: ""
author: ""
reviewer: "{{OWNER}}"
decision: "pending"
---

# {{TITLE}}

> _(Code review record — co-authored by a **Senior Engineer (Code Reviewer)** and an
> **AppSec Engineer**. Every PR is evaluated through both lenses in parallel: design,
> quality and tests on one side; security, privacy (LGPD) and secrets on the other.
> `status` tracks whether the review write-up is still being drafted or has been
> delivered; `decision` carries the outcome — pending / approved / approved-with-comments
> / changes-requested.)_

## Metadata

- **PR:** #<number> — [<url>]
- **Author:** <github-handle>
- **Reviewer(s):** {{OWNER}}
- **Branch:** `<feat/slug>` → `<base>`
- **Files changed:** <N>
- **Lines:** +<N> / −<N>
- **CI status at review time:** <green / red — link>

## Scope

Describe, in 1–2 paragraphs, what the PR does and which artifacts it touches. Call out
**what is intentionally out of scope** for this PR so the reviewer doesn't score it
against invisible criteria.

- **Related feature:** [[<feature>-design]]
- **Tasks covered:**
  - [[<feature>-tasks#TASK-NNN]]
- **Related ADRs / TRDs:** [[ADR-NNNN-<slug>]] · [[TRD-<slug>]]

---

## Review checklist

> The checklist is the **minimum** bar; missing a box is a `🔴 Blocker` unless the
> author and reviewer agree it does not apply and say so explicitly in §Findings.

### 1. Design & architecture (Code Reviewer lens)

- [ ] Architectural pattern fits the use case (Clean Architecture / DDD / SOLID / CQRS / Hexagonal — as the repo prescribes).
- [ ] Correct separation between Domain / Application / Infrastructure / Adapters; no upward dependencies.
- [ ] No unnecessary coupling, no abstraction leaks, no premature generality.
- [ ] Essential complexity ≥ accidental complexity — the change is not more complicated than the problem.
- [ ] Public surface (types, APIs, events) is consistent with existing patterns in the repo.

### 2. Code quality (Code Reviewer lens)

- [ ] Clear naming, readable intent, no clever-but-obscure constructs.
- [ ] No duplication that should have been abstracted (DRY) — and no premature abstraction (YAGNI).
- [ ] Correct error handling — no generic exceptions crossing domain boundaries, no silent swallows.
- [ ] No dead code, no unused variables, no obsolete comments, no TODOs without an owner.
- [ ] Follows repository conventions (formatter, lint, `CLAUDE.md` house rules).

### 3. Tests (Code Reviewer lens)

- [ ] Coverage ≥ `<N>%` on changed files (project default 85%).
- [ ] Edge cases covered: null, empty, boundary, concurrency, timezone, locale.
- [ ] Tests exercise **behavior**, not implementation — refactors should not break them.
- [ ] Property-Based Testing present where invariants/domain rules apply.
- [ ] Failure paths tested (retries, fallbacks, timeouts, poison messages).

### 4. AppSec (AppSec lens)

- [ ] **Injection** — SQL / command / LDAP / XPath / template injection paths closed; no raw user input reaching interpreters.
- [ ] **AuthN / AuthZ** — every new endpoint or handler enforces both; deny-by-default; tenant isolation preserved.
- [ ] **Sensitive data** — no PII / CPF / token / secret leaked to logs, responses, URLs, analytics, error pages.
- [ ] **Secrets** — nothing hardcoded; reads from the project secret manager; `.env`/credential files not committed.
- [ ] **Supply chain** — any new dependency is reviewed (license, maintenance, known CVEs); lockfile updated.
- [ ] **SSRF / CORS** — outbound calls respect allowlists; CORS is scoped to trusted origins only.
- [ ] **Rate limiting / DoS** — new critical or unauthenticated endpoints have throttling / quotas.
- [ ] **Error model** — 4xx/5xx responses use the repo error model (RFC 7807 where applicable); no internal stack / DB / framework details leaked to the client.
- [ ] **Crypto** — TLS ≥ 1.2 on every new hop; at-rest encryption through the project KMS for new sensitive fields.

### 5. Privacy & LGPD (AppSec lens)

- [ ] **Data minimization** — only fields required for the stated purpose are persisted / returned.
- [ ] **Masking** — CPF / e-mail / phone / token masked in every log, error, and analytics event.
- [ ] **Subject rights** — new personal-data paths support access / rectification / deletion.
- [ ] **Retention** — new personal data is classified and assigned a retention window.
- [ ] **Consent** — where required, consent capture is present and auditable.
- [ ] **Audit trail** — new sensitive actions write `actor / target / outcome / reason` to the append-only log.

### 6. Process & delivery

- [ ] Conventional Commits respected in the branch history.
- [ ] CI green (build, test, lint, type-check, SAST, SCA, image scan).
- [ ] Documentation updated in the same PR: `[[<feature>-design]]`, ADRs, runbooks, API reference.
- [ ] Rollback plan exists (for risky changes) and is cheap (feature flag / revert-safe migration / idempotent task).
- [ ] Observability updated: new logs carry `correlation_id`/`tenant_id`/`actor_id`, new metrics/dashboards/alerts exist for new critical paths.

---

## Findings

> Record each finding with **severity**, **location**, **problem**, **suggestion**. A finding
> without a location is not actionable — add `path/file.ext:NNN` or a unit of change.

### 🔴 Blocker — must fix before merge

- **File:** `path/file.ext:NNN`
- **Problem:** <what is wrong and why it matters>.
- **Suggestion:** <concrete fix>.

### 🟡 Major — should fix, not blocking

- **File:** `path/file.ext:NNN`
- **Problem:** <…>.
- **Suggestion:** <…>.

### 🟢 Minor / Nit — optional polish

- **File:** `path/file.ext:NNN`
- **Problem:** <…>.
- **Suggestion:** <…>.

### 🔵 Praise — worth preserving

- <what the author got right that the team should reinforce>.

---

## Decision

Set the `decision:` frontmatter field to exactly one of:

- `approved` — no changes required; safe to merge.
- `approved-with-comments` — merge allowed; suggestions are optional and tracked separately.
- `changes-requested` — mandatory fixes required before merge; re-review after fixes.
- `pending` — still writing the review; use `status: final` + a concrete decision to close.

**Rationale:** 1–3 sentences explaining the decision. Mandatory when `changes-requested` —
name the blockers.

---

## References

- [[<feature>-design]] — feature design the PR implements
- [[<branch-slug>]] — PR branch record (see `/sdlc-kit:worktree`)
- [[ADR-NNNN-<slug>]] — any ADR the PR implements or deviates from
- [[TRD-<slug>]] — any TRD the PR must comply with
- [[_INDEX]] — global index
