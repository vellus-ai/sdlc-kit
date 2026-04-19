---
type: spec-design
title: "Design — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 04
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [spec, design]
feature: "{{SLUG}}"
---

# Design — {{TITLE}}

> _(Co-authored by a **Senior Software Engineer**, an **AppSec Engineer** and a **Software Architect**.
> Every section below is deliberate engineering: best-practice patterns chosen for concrete problems,
> an explicit security posture, a data model that evolves cleanly, contracts that don't break
> consumers, and observability that lets you page on the right things.)_

## 1. Overview

Two paragraphs. Focus on **how** — the **what** lives in [[<feature>-requirements]].

- What we are building, in one sentence a new hire would understand.
- Why *this* shape and not the obvious alternative.

---

## 2. Architectural drivers

> The quality attributes that shape the design. Pulled from [[<feature>-requirements]] §7 (NFR).

| Driver | Source NFR | Target | Design implication |
|---|---|---|---|
| Latency p95 ≤ `<N>`ms | NFR-PERF-01 | `<N>`ms | Cache `<X>`, drop `<Y>` from hot path |
| Availability ≥ `<99.9%>` | NFR-REL-01 | `<99.9%>` | Active-active, circuit breakers on `<dep>` |
| Personal data in scope | NFR-PRIV-01 | LGPD | Pseudonymize at rest, mask in logs |
| Audit trail | NFR-COMP-02 | Immutable | Append-only event store |

---

## 3. Design principles & patterns

> State the engineering principles adopted for **this** feature and the patterns chosen, each with rationale.

### 3.1 Principles
- **<DDD | Hexagonal | Clean | CQRS | Event-driven | Functional core / imperative shell>** — *because* <reason>.
- **YAGNI / SOLID / DRY boundaries** — we explicitly accept <duplication X> to keep <module Y> independent.

### 3.2 Patterns in use (per problem)

| Problem | Pattern chosen | Rationale | Alternatives rejected |
|---|---|---|---|
| Cross-aggregate write | Saga (orchestration) | Explicit compensation; visible in logs | 2PC (operational burden), choreography (harder to debug) |
| Read model divergence | CQRS (read replica) | Tailor reads to UI; isolate write load | Same model (contention), materialized views (stale) |
| External API fragility | Circuit breaker + retry with jitter | Bounded blast radius | Plain retry (thundering herd), timeout only (no protection) |
| Inbound idempotency | Idempotency-Key header + request log | Required by NFR-REL-02 | Dedup by payload hash (collisions) |
| Background jobs | Outbox + consumer | Transactional consistency with DB | Direct publish (dual-write race) |

### 3.3 Explicit non-goals
- <simplification we accept — e.g. "no multi-region replication in v1">.
- <deferred capability — e.g. "no streaming export">.

---

## 4. System architecture (C4 – Container / Component)

Which services/containers/modules participate and how they collaborate. Reference the system's C4 when applicable.

```mermaid
flowchart LR
    subgraph Client
        UI[Web UI]
    end
    subgraph Edge
        GW[API Gateway]
    end
    subgraph App
        API[Backend API]
        SVC[Domain Service]
        W[Async Worker]
    end
    subgraph Data
        DB[(Primary DB)]
        RO[(Read Replica)]
        Q[(Message Bus)]
        CACHE[(Cache)]
    end

    UI --> GW --> API
    API --> SVC --> DB
    SVC --> Q --> W
    API --> CACHE
    API --> RO
```

### 4.1 New components
- **`<NewComponent>`** — responsibility, where it lives (`<path/in/code>`), interfaces it exposes.

### 4.2 Modified components
- **`<ExistingComponent>`** — what changes, contract impact, migration note.

### 4.3 Layering / module boundaries (hexagonal example)
- **Domain:** `<pure types + invariants>` (no I/O).
- **Application:** `<use cases / orchestration>` (ports in, ports out).
- **Adapters (inbound):** HTTP handlers, CLI, event consumer.
- **Adapters (outbound):** DB repo, HTTP client, pub/sub publisher.
- **Infrastructure:** `<container, config, observability wiring>`.

---

## 5. Main flows

> Document the happy path **and** at least one failure / compensation path. Keep sequence diagrams to essentials — link to code for detail.

### 5.1 Flow A — `<happy path name>`
1. User triggers `<X>`.
2. Frontend calls `<endpoint>`.
3. API validates `<schema>` and authenticates.
4. Service executes `<use case>` and persists.
5. Outbox publishes `<event>`.
6. Consumer projects into the read model.
7. Response returned to caller.

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant S as Service
    participant D as DB
    participant Q as Bus

    U->>F: Action
    F->>A: POST /resource (Idempotency-Key)
    A->>S: Create(cmd)
    S->>D: INSERT (+ outbox row)
    D-->>S: ok
    S-->>A: Resource
    A-->>F: 201 Created
    Note over S,Q: async
    S-->>Q: <event>
```

### 5.2 Flow B — `<failure / compensation>`
Describe the failure path: what happens when `<dependency X>` fails, how we compensate, what the user sees.

---

## 6. Data model

### 6.1 Conceptual model
Aggregates, entities and value objects (DDD). One paragraph per aggregate; invariants explicit.

### 6.2 Physical schema

```sql
CREATE TABLE <table> (
  id            UUID        PRIMARY KEY,
  tenant_id     UUID        NOT NULL,
  field_a       TEXT        NOT NULL,
  field_b       INTEGER     NOT NULL,
  status        TEXT        NOT NULL CHECK (status IN ('x','y','z')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER     NOT NULL DEFAULT 1
);

CREATE INDEX idx_<table>_tenant_status ON <table>(tenant_id, status);
-- Justify each index with the query it serves.
```

### 6.3 Indexing strategy
| Index | Query it serves | Cardinality note |
|---|---|---|
| `idx_<table>_tenant_status` | "list open items for tenant X" | high selectivity on tenant_id |

### 6.4 Consistency & transactions
- **Consistency model:** strong within aggregate, eventual across aggregates (via outbox).
- **Transaction boundaries:** one aggregate per transaction; cross-aggregate writes via saga.
- **Concurrency control:** optimistic locking (`version` column) / `SELECT … FOR UPDATE` on `<path>`.

### 6.5 Migrations & evolution
- `<N>_<description>.up.sql` / `.down.sql` — additive only; no destructive changes without expand/contract.
- **Expand/contract plan** for breaking schema changes: expand → dual-write → backfill → cutover read → contract.
- **Backfill strategy:** <batched job / lazy on read / one-shot — include volume, duration and risk>.

### 6.6 Data classification
| Field | Class (public / internal / personal / sensitive) | At-rest treatment | In-transit | In logs |
|---|---|---|---|---|
| `email` | personal | encrypted (KMS) | TLS | masked |
| `cpf` | sensitive (LGPD) | encrypted + tokenized | TLS | never logged |

---

## 7. Contracts (inbound & outbound)

### 7.1 Synchronous APIs (REST / gRPC)

| Endpoint | Method | Auth | Idempotent? | Versioning |
|---|---|---|---|---|
| `/v1/<resource>` | POST | OIDC | yes (Idempotency-Key) | URI-versioned |

- **OpenAPI / proto source:** `<path/to/spec>` — keep the spec as the source of truth; code generated or validated against it.
- **Error model:** [RFC 7807 `application/problem+json`](https://www.rfc-editor.org/rfc/rfc7807) with `type`, `title`, `status`, `detail`, `instance`, `correlation_id`.
- **Backwards compatibility:** additive only within a major version; breaking change → new major + deprecation notice.

### 7.2 Asynchronous events

| Event | Direction | Schema | Semantics | Partition key |
|---|---|---|---|---|
| `<feature>.<entity>.created.v1` | emitted | AsyncAPI / Avro | at-least-once | `tenant_id` |
| `<dep>.<entity>.updated.v1` | consumed | … | at-least-once | … |

- **Delivery guarantees:** at-least-once → consumers **must** be idempotent (state `<key>` used).
- **Dead-letter / retry:** <queue name, retry policy, poison-message handling>.
- **Schema registry:** <registry URL / versioning policy>.

### 7.3 External integrations
- **Third-party APIs:** <vendor, SLA, auth, rate limits, circuit-breaker params>.
- **Webhooks we receive:** <path, signature verification, replay protection>.

---

## 8. Security design (AppSec)

> Threat-model before implementation. Treat this section as a merge gate.

### 8.1 Trust boundaries
Annotate the architecture diagram's boundaries: client ↔ edge ↔ API ↔ data. Every arrow that crosses a boundary is a threat surface.

### 8.2 STRIDE per component

| Component | Spoofing | Tampering | Repudiation | Info disclosure | DoS | Elevation of privilege |
|---|---|---|---|---|---|---|
| API | OIDC + mTLS | payload signing | audit log | TLS, no PII in logs | rate limit, WAF | RBAC, deny-by-default |
| Worker | service identity | message signing | audit trail | encrypted queue | backpressure | least-privilege IAM |
| DB | — | row-level checksums | WAL | encryption at rest | connection pool cap | per-service role |

### 8.3 AuthN & AuthZ
- **AuthN:** `<OIDC issuer / mTLS cert / HMAC>` — token lifetime, refresh strategy, revocation.
- **AuthZ:** `<RBAC / ABAC / relationship-based>` — policy source, evaluation point (gateway vs. service), deny-by-default.

### 8.4 Input validation & output encoding
- Validate at the boundary (`<schema lib>`); never pass unvalidated input to SQL/shell/template.
- Output encoding: HTML-escape in UI; parameterized queries in DB; structured logging (no string concatenation).

### 8.5 Secrets & key management
- **Source:** `<secret manager / KMS>`; forbidden in source, `.env` files, container images or logs.
- **Rotation:** <N days; automated>.
- **Envelope encryption:** for sensitive fields at rest.

### 8.6 Privacy (LGPD / GDPR)
- **Data minimization:** only the fields in §6.6 class "personal"/"sensitive".
- **Subject rights endpoints:** access / rectification / deletion — latency ≤ `<N>`d.
- **Data residency:** <region>; cross-border transfers note.

### 8.7 Dependency & supply chain
- **SBOM:** generated on build; scanned (Trivy / Grype / Snyk).
- **Vulnerability SLA:** critical fixed in `<N>`d; high in `<N>`d.
- **Signed images:** Cosign + KMS; only signed images allowed to deploy.

### 8.8 Logging & telemetry hardening
- PII/secret scrubber in the logger; deny-list plus per-field class from §6.6.
- Audit log is append-only and tamper-evident.

---

## 9. Observability

### 9.1 SLIs & SLOs

| SLI | Definition | SLO | Error budget |
|---|---|---|---|
| Request success rate | `1 - (5xx / total)` on `<critical path>` | ≥ 99.9% monthly | 43m/month |
| Latency p95 | server-side latency on `<critical path>` | ≤ `<N>`ms | — |

### 9.2 Logs (structured)
- Format: JSON with `timestamp`, `level`, `service`, `env`, `correlation_id`, `tenant_id`, `actor_id`, `event`.
- Levels: reserve `error` for actionable conditions.
- Sampling: full retention on `error`; sampled on `info`.

### 9.3 Metrics (RED + USE)
- **RED (request-oriented):** `<feature>_requests_total{status}`, `<feature>_request_duration_seconds_bucket`, `<feature>_errors_total{type}`.
- **USE (resource-oriented):** utilization, saturation, errors for DB pool, queue depth, cache hit ratio.

### 9.4 Traces (OpenTelemetry)
- Span per inbound request and per outbound call; baggage carries `correlation_id` and `tenant_id`.
- Attributes: `http.*`, `db.*`, `messaging.*`, plus domain-specific `<feature>.<entity>.id`.

### 9.5 Dashboards & alerts
- **Dashboard:** <URL / file path>.
- **Alerts:** SLO burn rate (`2%/1h` fast, `10%/6h` slow); queue depth > `<N>`; dead-letter > 0.
- **Runbook link:** [[<feature>-runbook]] or `<URL>`.

---

## 10. Performance & capacity plan

- **Load profile:** `<N>` req/s peak, `<N>` req/s steady.
- **Performance budget per layer:** client `<N>`ms + edge `<N>`ms + API `<N>`ms + DB `<N>`ms ≤ total `<N>`ms.
- **Hot paths / N+1 audit:** explicit list of queries and their expected plan.
- **Load test plan:** `<k6 / Gatling script path>`; pass criteria mapped to NFR-PERF-*.

---

## 11. Resilience & failure modes

| Failure | Detection | Response | Recovery |
|---|---|---|---|
| DB primary down | health check + error rate | read-only mode from replica | promote replica; replay outbox |
| Queue backpressure | queue depth metric | shed load, return `503 Retry-After` | scale consumer; drain DLQ |
| 3rd-party API timeout | circuit breaker | cached/degraded response | half-open probe |

Patterns: **circuit breaker**, **bulkhead**, **timeout + retry with jitter**, **graceful degradation**, **idempotent consumers**, **outbox**, **saga compensations**.

---

## 12. Deployment & rollout

- **Environments:** dev → staging → canary → production.
- **Feature flag:** `<flag key>` — ramp plan (1% → 10% → 50% → 100%), kill-switch path.
- **Migration ordering:** schema first (expand) → code → backfill → cutover → contract.
- **Rollback strategy:** versioned image + DB `down.sql` up to `<commit>`; data-loss boundary documented.

---

## 13. Testing strategy (hand-off to `tasks.md`)

- **Unit:** domain pure; property-based where invariants are cheap to express.
- **Contract:** provider + consumer tests for every inbound/outbound API and event.
- **Integration:** real DB + real bus in a disposable environment.
- **E2E / smoke:** happy path per user story on every deploy.
- **Security tests:** authn/authz negative cases; SAST / SCA / image scan in CI.
- **Performance:** k6 against staging with the load profile in §10.
- **Chaos:** latency & failure injection on `<dependency>` in staging.

---

## 14. Local decisions

> Decisions that affect only this feature and don't warrant a full ADR. Structural or cross-feature decisions → `/sdlc-kit:adr`.

- **LD-01 — <decision>.** Context → options → choice → consequence.
- **LD-02 — <decision>.** …

---

## 15. Technical risks

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| <risk> | L/M/H | L/M/H | <mitigation> | <name> |

---

## 16. Open questions

- <question + who owns the answer + by when>

---

## References

- **Requirements:** [[<feature>-requirements]]
- **Tasks:** [[<feature>-tasks]]
- **ADRs:** [[ADR-NNNN-<slug>]]
- **C4:** [[container]] / [[component]]
- **Domain model:** [[<bounded-context>]]
- **TRD (cross-cutting NFRs):** [[TRD-<slug>]]
- [[_INDEX]] — global index
