---
type: spec-requirements
title: "Requirements — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 04
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [spec, requirements, ears]
feature: "{{SLUG}}"
epic: ""
---

# Requirements — {{TITLE}}

> _(Co-authored by a **Senior Product Manager**, a **Software Engineer** and a **Solutions Architect**.
> Functional and non-functional requirements are mapped end-to-end, testable, traceable to tasks, and
> aligned with the product strategy, the technical feasibility and the target solution architecture.)_

## 1. Product context

### 1.1 Problem statement
Describe, in 1–2 paragraphs, the user/business problem this feature solves. What hurts today? Who feels the pain?

### 1.2 Target users & personas
- **Primary persona:** <name — one-line description>.
- **Secondary persona(s):** <name — one-line description>.
- **Anti-persona / not the audience:** <who this is not for>.

### 1.3 Business outcome & success metrics
Measurable outcomes the product owner will inspect after ship.

| KPI / Signal | Baseline | Target | Measurement window | Source |
|---|---|---|---|---|
| <metric> | <current> | <goal> | <e.g. 30d post-launch> | <analytics/db/event> |

### 1.4 Strategic alignment
- **Parent initiative (PRD):** [[<prd-slug>]]
- **Parent epic:** [[<epic-slug>]]
- **Related OKR / theme:** <OKR ID or theme>.

---

## 2. Scope

### 2.1 In scope
What this feature does (2–3 paragraphs). Keep it concrete; link to user flows when useful.

### 2.2 Out of scope (explicit)
- <item that will NOT be done in this feature>
- <item deferred to another spec>

### 2.3 Assumptions
- **Assumption A:** <taken as true — e.g. "table X already exists">.
- **Assumption B:** <…>.

### 2.4 Dependencies
- **Upstream (we consume):** <team/service/feature>.
- **Downstream (consumes us):** <team/service/feature>.
- **External (outside our control):** <vendor / regulator / 3rd-party API>.

---

## 3. Actors & triggers

| Actor | Kind (user / system / timer) | Trigger |
|---|---|---|
| <persona or system> | <user / service / cron> | <user action / event / schedule> |

---

## 4. User stories

Story format: `As a <persona>, I want <capability>, so that <outcome>.`

### US-01 — <title>
- **Story:** As a <persona>, I want <capability>, so that <outcome>.
- **Covers requirements:** REQ-001, REQ-002
- **Linked tasks:** [[<feature>-tasks#TASK-010]]

### US-02 — <title>
- **Story:** As a <persona>, I want <capability>, so that <outcome>.
- **Covers requirements:** REQ-003
- **Linked tasks:** [[<feature>-tasks#TASK-020]]

---

## 5. EARS notation (how to write each requirement)

All functional requirements below use EARS (Easy Approach to Requirements Syntax). Pick one format per REQ:

1. **Ubiquitous:** `THE SYSTEM SHALL <behavior>`
2. **Event-driven:** `WHEN <trigger> THE SYSTEM SHALL <behavior>`
3. **State-driven:** `WHILE <state> THE SYSTEM SHALL <behavior>`
4. **Optional feature:** `WHERE <feature enabled> THE SYSTEM SHALL <behavior>`
5. **Event + precondition:** `WHEN <trigger> IF <precondition> THE SYSTEM SHALL <behavior>`

---

## 6. Functional requirements (FR)

> Every FR carries: **priority** (MoSCoW), **EARS statement**, at least one **testable acceptance criterion** (`Given / When / Then`), and a link to the task(s) that implement it. Orphan FRs (no task) or orphan TASKs (no FR) are a review blocker.

### REQ-001 — <short title>
- **Priority:** must / should / could / won't (MoSCoW).
- **Statement:**
  > `WHEN <trigger> IF <precondition> THE SYSTEM SHALL <behavior>`
- **Acceptance criteria (testable):**
  - Given <initial state>, when <action>, then <observable result>.
  - Given <edge state>, when <action>, then <observable result>.
- **Rationale:** <why this requirement exists — link to persona/business outcome>.
- **Linked task(s):** [[<feature>-tasks#TASK-001]]

### REQ-002 — <short title>
- **Priority:** must
- **Statement:** `WHILE <state> THE SYSTEM SHALL <behavior>`
- **Acceptance criteria:** <Given/When/Then>.
- **Rationale:** <…>
- **Linked task(s):** [[<feature>-tasks#TASK-002]]

### REQ-003 — <short title>
- **Priority:** should
- **Statement:** `THE SYSTEM SHALL <behavior>`
- **Acceptance criteria:** <Given/When/Then>.
- **Rationale:** <…>
- **Linked task(s):** [[<feature>-tasks#TASK-003]]

---

## 7. Non-functional requirements (NFR)

> Feature-specific NFRs only. Cross-cutting NFRs belong in a TRD (`[[TRD-<slug>]]`) — link and do not duplicate.
> Every NFR must be **testable**: state the metric, the target, and how it will be measured.

### 7.1 Performance
- **NFR-PERF-01 — Latency p95 of `<critical path>`.** `THE SYSTEM SHALL` respond in ≤ `<N>`ms at p95 under `<load profile>`. *Measured via:* <dashboard / k6 test>.
- **NFR-PERF-02 — Throughput.** `THE SYSTEM SHALL` sustain ≥ `<N>` req/s at `<CPU%>` per pod.

### 7.2 Scalability & capacity
- **NFR-SCAL-01 — Horizontal scaling.** `THE SYSTEM SHALL` scale linearly up to `<N>` pods; state the bottleneck (DB, cache, queue).
- **NFR-SCAL-02 — Data volume.** `THE SYSTEM SHALL` operate within SLOs up to `<row count / storage>`.

### 7.3 Reliability & availability
- **NFR-REL-01 — Availability SLO.** `THE SYSTEM SHALL` achieve ≥ `<99.9%>` monthly availability for `<critical path>`. Error budget: `<minutes/month>`.
- **NFR-REL-02 — Recovery.** `WHEN <dependency X> fails THE SYSTEM SHALL` degrade to `<fallback>` and recover within `<MTTR>`.
- **NFR-REL-03 — Backup / RPO / RTO.** `THE SYSTEM SHALL` meet RPO ≤ `<N>`min and RTO ≤ `<N>`min.

### 7.4 Security
- **NFR-SEC-01 — AuthN.** `THE SYSTEM SHALL` require `<OIDC / mTLS / HMAC>` on every endpoint except `<allowlist>`.
- **NFR-SEC-02 — AuthZ.** `THE SYSTEM SHALL` enforce `<RBAC / ABAC>` on every resource access.
- **NFR-SEC-03 — Input validation.** `THE SYSTEM SHALL` reject malformed input with `4xx` and never pass raw input to `<SQL / shell / template>`.
- **NFR-SEC-04 — Secrets.** `THE SYSTEM SHALL` read secrets only from `<secret manager>`; forbidden in source, env files committed, or logs.
- **NFR-SEC-05 — Transport.** `THE SYSTEM SHALL` require TLS ≥ 1.2 on every network hop.

### 7.5 Privacy & compliance (LGPD / GDPR / sector-specific)
- **NFR-PRIV-01 — Data minimization.** `THE SYSTEM SHALL` persist only `<fields required for purpose>`; everything else is forbidden.
- **NFR-PRIV-02 — Subject rights.** `THE SYSTEM SHALL` support access, rectification and deletion of personal data within `<N>`d.
- **NFR-PRIV-03 — Data masking.** `THE SYSTEM SHALL` mask `<CPF / e-mail / phone>` in every log, error, and analytics event.
- **NFR-COMP-01 — Retention.** `THE SYSTEM SHALL` retain `<data class>` for `<N>` days and purge after.
- **NFR-COMP-02 — Audit trail.** `WHEN <sensitive action> occurs THE SYSTEM SHALL` record actor, target, outcome and reason into an immutable audit log.

### 7.6 Observability
- **NFR-OBS-01 — Structured logs.** `THE SYSTEM SHALL` emit JSON logs with `correlation_id`, `tenant_id`, `actor_id` on every critical operation.
- **NFR-OBS-02 — Metrics.** `THE SYSTEM SHALL` expose `<RED / USE>` metrics (rate, errors, duration) for each endpoint.
- **NFR-OBS-03 — Traces.** `THE SYSTEM SHALL` emit OpenTelemetry spans covering `<critical path>`.
- **NFR-OBS-04 — Alerts.** `THE SYSTEM SHALL` page on SLO burn rate ≥ `<2%>/h`.

### 7.7 Accessibility & usability
- **NFR-A11Y-01 — WCAG.** `THE SYSTEM SHALL` comply with WCAG 2.1 Level AA on every user-facing screen.
- **NFR-UX-01 — Error messages.** `THE SYSTEM SHALL` surface actionable, user-facing messages in `<language>` on every 4xx.

### 7.8 Maintainability & quality
- **NFR-MAIN-01 — Test coverage.** `THE SYSTEM SHALL` ship with ≥ `<85%>` coverage on changed files.
- **NFR-MAIN-02 — Linter gates.** `THE SYSTEM SHALL` pass `<linter / type-checker>` before merge.
- **NFR-MAIN-03 — Docs.** `THE SYSTEM SHALL` ship with updated `[[<feature>-design]]` and ADRs for structural decisions.

### 7.9 Portability & internationalization
- **NFR-I18N-01 — Locale.** `THE SYSTEM SHALL` support `<pt-BR, en-US>` for all user-facing strings.
- **NFR-PORT-01 — Runtime.** `THE SYSTEM SHALL` run on `<stack / container runtime / cloud>`.

### 7.10 Cost
- **NFR-COST-01 — Budget.** `THE SYSTEM SHALL` stay within `<$ / month>` at `<load profile>`.

---

## 8. Edge cases & failure modes

> The triad's failure brainstorm — one line per edge case; every one must map to an acceptance criterion or an explicit "tolerated" note.

- **Empty / null / boundary inputs:** <expected behavior>.
- **Concurrent writes / races:** <strategy>.
- **Upstream dependency down:** <fallback / retry / circuit breaker>.
- **Partial failure mid-operation:** <compensation / idempotency>.
- **Timezone / locale / i18n drift:** <expected behavior>.
- **Rate-limit / abuse:** <limit and response>.

---

## 9. Explicitly out of scope

- <item that will NOT be done here — link to the spec that will, if any>
- <item deferred>

---

## 10. Traceability matrix

> Maintained throughout the trio. A requirement with no task is an implementation gap; a task with no requirement is scope creep.

| Requirement | User story | Task(s) | Acceptance-criterion test |
|---|---|---|---|
| REQ-001 | US-01 | [[<feature>-tasks#TASK-010]] | <test file / scenario> |
| REQ-002 | US-01 | [[<feature>-tasks#TASK-011]] | <test file / scenario> |
| REQ-003 | US-02 | [[<feature>-tasks#TASK-020]] | <test file / scenario> |
| NFR-PERF-01 | — | [[<feature>-tasks#TASK-050]] | <k6 scenario> |

---

## 11. Open questions

- <question + who owns the answer + by when>

---

## References

- **Epic:** [[<epic-slug>]]
- **PRD:** [[<prd-slug>]]
- **TRD (cross-cutting NFRs):** [[TRD-<slug>]]
- **Design:** [[<feature>-design]]
- **Tasks:** [[<feature>-tasks]]
- [[_INDEX]] — global index
