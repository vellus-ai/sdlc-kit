---
type: trd
title: "{{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-trd
owner: "{{OWNER}}"
tags: [architecture, trd, nfr]
scope: "cross-feature"
---

# {{TITLE}}

> _(Technical Requirements Document — **cross-cutting** non-functional requirements
> shared by multiple features/services. Co-authored by a **Software Architect**,
> an **AppSec Engineer** and an **SRE / Platform Engineer**. Each requirement is
> testable, measurable, and inherits down into individual feature specs via
> `[[<feature>-requirements]]` § Non-functional requirements.)_

## 1. Scope

### 1.1 Applies to
- **Services / domains in scope:** <list services / bounded contexts>.
- **Features inheriting these NFRs:** <link or list — explicit > implicit>.

### 1.2 Does NOT apply to
- <out-of-scope service / domain — link to the TRD that does cover it, if any>.

### 1.3 Relationship to other documents
- **Parent C4:** [[context]] / [[container]].
- **Related TRDs:** [[TRD-<other-slug>]].
- **Related ADRs:** [[ADR-NNNN-<slug>]].

---

## 2. Motivation

Why this TRD exists, in 2–3 paragraphs. Cover:
- The cross-cutting risk or opportunity it addresses.
- What was happening (or would happen) without a shared baseline.
- The business / regulatory / operational driver.

---

## 3. Governance

| Field | Value |
|---|---|
| **Owner** | `{{OWNER}}` |
| **Decision authority** | <name / role — who approves changes to this TRD> |
| **Review cadence** | <quarterly / on-incident / on-architecture-change> |
| **Exception process** | <how a feature requests a documented deviation — typically an ADR linking back to this TRD> |
| **Effective from** | {{DATE}} |
| **Sunset / next review by** | <YYYY-MM-DD> |

---

## 4. Cross-cutting non-functional requirements

> Mirror the taxonomy used in `04-specs/_templates/requirements.md.tpl` § 7 so feature specs can either
> inherit ("complies with [[<this-trd>]]") or call out a justified deviation. Every requirement is
> **testable**: name the metric, the target, and the measurement method.

### 4.1 Performance

- **TRD-PERF-01 — p95 latency on critical paths.** `THE PLATFORM SHALL` keep p95 ≤ `<N>`ms for any user-facing synchronous call. *Measured via:* <dashboard / SLI source>.
- **TRD-PERF-02 — Throughput baseline.** `THE PLATFORM SHALL` sustain ≥ `<N>` req/s per pod at `<CPU%>` headroom.
- **TRD-PERF-03 — End-to-end response budget.** `THE PLATFORM SHALL` deliver perceived response within `<N>`s on the median user device / network.

### 4.2 Scalability & capacity

- **TRD-SCAL-01 — Peak vs. steady.** `THE PLATFORM SHALL` absorb `<N>×` peak over steady load without SLO regression.
- **TRD-SCAL-02 — Horizontal scaling.** `THE PLATFORM SHALL` scale stateless services horizontally up to `<N>` pods; state the bottleneck (DB / cache / queue).
- **TRD-SCAL-03 — Data volume ceilings.** `THE PLATFORM SHALL` operate within SLO up to `<rows / GB / events-per-day>`; document the partition / sharding plan beyond.

### 4.3 Reliability & availability

- **TRD-REL-01 — Availability SLO.** `THE PLATFORM SHALL` achieve ≥ `<99.9%>` monthly availability per critical service. **Error budget:** `<43m / month>`.
- **TRD-REL-02 — Recovery objectives.** `THE PLATFORM SHALL` meet **RTO ≤ `<N>`min** and **RPO ≤ `<N>`min** for tier-1 data stores.
- **TRD-REL-03 — Backups & restore drills.** `THE PLATFORM SHALL` exercise a full restore at least `<frequency>`.
- **TRD-REL-04 — Multi-AZ / multi-region.** `THE PLATFORM SHALL` deploy critical services across `<≥2 AZs / regions>`.

### 4.4 Security

- **TRD-SEC-01 — AuthN baseline.** `THE PLATFORM SHALL` use `<OIDC / mTLS / HMAC>`; no anonymous endpoints except `<allowlist>`.
- **TRD-SEC-02 — AuthZ baseline.** `THE PLATFORM SHALL` enforce `<RBAC / ABAC>` deny-by-default, evaluated at `<gateway / service>`.
- **TRD-SEC-03 — Encryption.** `THE PLATFORM SHALL` enforce TLS ≥ 1.2 in transit and `<KMS-managed>` encryption at rest for tier-1 data.
- **TRD-SEC-04 — Secrets.** `THE PLATFORM SHALL` source secrets only from `<secret manager>`; rotation policy `<N>`d; no secrets in source / images / logs.
- **TRD-SEC-05 — Supply chain.** `THE PLATFORM SHALL` ship signed images (Cosign + KMS); deploy gate rejects unsigned. SBOM generated and scanned every build.
- **TRD-SEC-06 — Vulnerability SLA.** Critical vulns fixed within `<N>`d; high within `<N>`d.
- **TRD-SEC-07 — Threat-model gate.** `THE PLATFORM SHALL` require a STRIDE pass on every new exposed surface before launch.

### 4.5 Privacy & compliance (LGPD / GDPR / sector-specific)

- **TRD-PRIV-01 — Data minimization.** `THE PLATFORM SHALL` persist personal data only for documented purposes.
- **TRD-PRIV-02 — Subject rights.** `THE PLATFORM SHALL` honor access / rectification / deletion within `<N>`d.
- **TRD-PRIV-03 — Masking & redaction.** `THE PLATFORM SHALL` mask `<CPF / e-mail / phone / token>` in every log, error, and analytics event.
- **TRD-COMP-01 — Retention.** `THE PLATFORM SHALL` retain data per the retention matrix below.
- **TRD-COMP-02 — Audit trail.** `THE PLATFORM SHALL` write actor / target / outcome to an append-only, tamper-evident audit log for every sensitive action.

| Data class | Examples | Retention | Storage | Logging |
|---|---|---|---|---|
| Public | marketing pages | indefinite | any | full |
| Internal | feature flags | `<N>`d | encrypted | full |
| Personal | e-mail, name | `<N>`d | KMS-encrypted | masked |
| Sensitive (LGPD) | CPF, payment | `<N>`d | KMS + tokenized | never logged |

### 4.6 Observability

- **TRD-OBS-01 — Structured logs.** `THE PLATFORM SHALL` emit JSON logs with `correlation_id`, `tenant_id`, `actor_id`, `service`, `env` on every request.
- **TRD-OBS-02 — Metrics (RED + USE).** `THE PLATFORM SHALL` expose request rate / errors / duration per endpoint, plus utilization / saturation / errors per shared resource.
- **TRD-OBS-03 — Traces.** `THE PLATFORM SHALL` emit OpenTelemetry spans across every inbound and outbound hop; baggage carries `correlation_id` and `tenant_id`.
- **TRD-OBS-04 — Alerting.** `THE PLATFORM SHALL` page on **SLO burn rate** (`2%/1h` fast / `10%/6h` slow), DLQ > 0, and saturation thresholds.
- **TRD-OBS-05 — Runbooks.** `THE PLATFORM SHALL` keep a runbook linked from every alert.

### 4.7 Accessibility & usability

- **TRD-A11Y-01 — WCAG.** `THE PLATFORM SHALL` comply with WCAG 2.1 Level AA on every user-facing surface (see `/sdlc-kit:design-system` for the per-criterion checklist).
- **TRD-UX-01 — Error model.** `THE PLATFORM SHALL` surface RFC 7807 problem details on every 4xx/5xx, with localized user-facing message.

### 4.8 Maintainability & quality gates

- **TRD-MAIN-01 — Test coverage.** `THE PLATFORM SHALL` enforce ≥ `<85%>` coverage on changed files in CI.
- **TRD-MAIN-02 — Linter / type-check / security gates.** `THE PLATFORM SHALL` block merges that fail `<linter>` / `<type-checker>` / SAST / SCA / image scan.
- **TRD-MAIN-03 — Conventional Commits.** `THE PLATFORM SHALL` require Conventional Commits on branches and commits (see `tasks.md` invariants).
- **TRD-MAIN-04 — Docs as code.** `THE PLATFORM SHALL` update `[[<feature>-design]]` and any affected ADRs in the same PR as the code change.

### 4.9 Portability & internationalization

- **TRD-I18N-01 — Locales.** `THE PLATFORM SHALL` support `<pt-BR, en-US>` for all user-facing copy.
- **TRD-PORT-01 — Runtime.** `THE PLATFORM SHALL` run on `<container runtime / orchestrator / cloud>` with no host-specific assumptions outside the IaC layer.

### 4.10 Cost

- **TRD-COST-01 — Unit cost ceiling.** `THE PLATFORM SHALL` keep cost per `<unit — request, tenant, GB>` below `<$ value>` at `<load profile>`.
- **TRD-COST-02 — Idle / off-peak.** `THE PLATFORM SHALL` scale down to `<N>` replicas off-peak.

---

## 5. SLIs & SLOs (consolidated)

| SLI | Definition | SLO target | Window | Error budget | Burn alert |
|---|---|---|---|---|---|
| Availability | `1 − (5xx / total)` on critical paths | ≥ 99.9% | 30d | 43m / month | `2%/1h` fast, `10%/6h` slow |
| p95 latency | server-side latency on critical path | ≤ `<N>`ms | 5m | — | > `<N>`ms |
| Error rate | error responses / total | ≤ 0.1% | 5m | — | > 0.5% |
| Queue lag | newest age in DLQ | ≤ `<N>`s | 1m | — | DLQ > 0 |

---

## 6. High-level architecture (reference)

Brief description of the platform shape this TRD assumes. Reference C4 when it exists.

```mermaid
flowchart LR
    A[Client] --> B[Gateway]
    B --> C[Service]
    C --> D[(DB)]
    C --> E[(Bus)]
```

---

## 7. Impacts on existing systems

- **`<System A>`** — what must change to comply with this TRD; effort estimate; owner.
- **`<System B>`** — …

---

## 8. Compliance & exception process

- **Compliance evidence:** how a feature demonstrates it meets each TRD-* (test, dashboard, audit log query).
- **Exception request:** any deviation requires an **ADR** referencing this TRD, justifying the deviation, listing the compensating control, and naming the sunset date for the exception.
- **Audit cadence:** the owner reviews exceptions every `<N>`d.

---

## 9. Technical risks

| Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|
| <risk> | L / M / H | L / M / H | <action> | <name> |

---

## 10. Open questions

- <question + who owns the answer + by when>

---

## References

- **C4:** [[context]] / [[container]]
- **Related ADRs:** [[ADR-NNNN-<slug>]]
- **Related TRDs:** [[TRD-<other-slug>]]
- **Inheriting feature specs:** [[<feature>-requirements]]
- [[_INDEX]] — global index
