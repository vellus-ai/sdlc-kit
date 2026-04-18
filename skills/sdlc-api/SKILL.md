---
name: sdlc-api
description: |
  Use when the user asks to document an API, design a REST endpoint, create an
  async event contract, define a gRPC service, specify a webhook, or when they
  invoke `/sdlc-kit:api`. Mirror triggers such as "document an API", "design a
  REST endpoint", "create async event contract", "webhook spec", "documentar
  API", "desenhar endpoint", "novo contrato de evento", "especificação de
  webhook", "contrato de API", "API assíncrona", "serviço gRPC". Operates
  under `02-architecture/api/` with four kinds, all collections — `rest`,
  `async`, `grpc`, `webhook` (one file per slug per kind). Lifecycle for every
  kind is `draft → approved → deprecated`. The skill scaffolds the file and
  records the status change; the **API Designer / Platform Engineer** and
  **Senior Software Engineer (consumer perspective)** drive the content
  interview together (producer contract vs consumer ergonomics), and the LLM
  mirrors the user's chat language when filling the template.
---

# sdlc-kit:api

Captures the **API / interface contracts** a system exposes or consumes,
under `02-architecture/api/`. Every external boundary — synchronous HTTP,
message bus, RPC, webhook callback — gets its own durable spec. The skill is
co-authored by two lenses working in tandem:

- **API Designer / Platform Engineer lens** — owns the **producer contract**.
  Source of truth for versioning strategy, auth model, SLA, rate limits,
  error taxonomy, backward-compat rules, schema evolution, observability
  emitted by the server side.
- **Senior Software Engineer (consumer perspective) lens** — owns the
  **consumer experience**. Source of truth for ergonomics, idempotency,
  pagination, error handling semantics, retry policy, client SDK
  affordances, and whether the API is pleasant to integrate against.

Every scaffolded file lands in `draft`. It only becomes `approved` after
both lenses review and agree the contract is production-grade. `deprecated`
preserves history so consumers can coordinate migrations; records are
**never deleted** — see Guardrails.

## Kinds, paths and templates

| Kind      | Type slug (frontmatter) | Cardinality           | Path                                    | Template                                        |
|-----------|-------------------------|-----------------------|-----------------------------------------|-------------------------------------------------|
| `rest`    | `api-rest`              | Collection (per slug) | `02-architecture/api/rest/<slug>.md`    | `_templates/api/rest.md.tpl`                    |
| `async`   | `api-async`             | Collection (per slug) | `02-architecture/api/async/<slug>.md`   | `_templates/api/async.md.tpl`                   |
| `grpc`    | `api-grpc`              | Collection (per slug) | `02-architecture/api/grpc/<slug>.md`    | `_templates/api/grpc.md.tpl`                    |
| `webhook` | `api-webhook`           | Collection (per slug) | `02-architecture/api/webhook/<slug>.md` | `_templates/api/webhook.md.tpl`                 |

All four kinds are collections — `--slug` is always required.

## Which kind should I pick?

| Situation                                                                    | Kind      |
|------------------------------------------------------------------------------|-----------|
| Synchronous HTTP request/response API, OpenAPI-ready                         | `rest`    |
| Message-bus / event-stream contract (Kafka, RabbitMQ, SNS/SQS, Pub/Sub)      | `async`   |
| RPC-style typed interface over HTTP/2, Protobuf-based                        | `grpc`    |
| Outbound HTTP callback the platform emits to customer/partner systems        | `webhook` |

If an API exists in two styles (e.g., same resource exposed via `rest` and
`grpc`), scaffold two records — one per kind — and cross-link them.

## Lifecycle

```
draft  →  approved  →  deprecated
```

- **`draft`** — scaffolded, under active design. Consumers must NOT rely on
  it; everything may change.
- **`approved`** — both lenses signed off. Producers guarantee the contract
  per the stated SLA/versioning policy; consumers may integrate.
- **`deprecated`** — superseded or retired. Kept in the vault forever so
  existing integrators can find the migration note. New work must cite the
  successor.

## When to invoke

- User says *"document the <X> API"*, *"design a REST endpoint for <Y>"*,
  *"new webhook for <Z>"*, *"desenhar o contrato assíncrono de <W>"* →
  scaffold the right kind and walk the template.
- User introduces a new external boundary (a new topic, a new gRPC service,
  a new public REST surface) → scaffold the record before code is written.
- A contract is reviewed and ready for consumers to rely on →
  `transition --to approved`.
- An API is being retired in favour of a new one → scaffold the replacement
  first, then `transition --to deprecated` the old record and add a
  `Superseded by [[<new-slug>]]` note in the body.

## When **not** to invoke

- Internal function signatures, class interfaces, or module boundaries
  inside a single service. Those belong to the code, not to the vault.
- DDD domain contracts between bounded contexts → that's
  `/sdlc-kit:domain` kind `contract` (strategic pattern: ACL, OHS,
  Conformist, etc.). A `domain-contract` describes the *integration pattern*
  between contexts; an `api-*` record describes the *wire protocol* used to
  realise that pattern.
- C4 container / component views → that's `/sdlc-kit:c4`.
- Cross-cutting NFRs (latency budgets, availability SLOs, rate-limit
  policies) → those live in the relevant `/sdlc-kit:trd` and get *cited*
  from the API spec, not duplicated.

## Flow

### 1. Pre-flight
- Read the target vault's `CLAUDE.md` if it exists — project-specific
  conventions (auth scheme, versioning style, error taxonomy) may override
  the template defaults.
- Run `list` first. **Never scaffold on top of an existing file without
  `--force`**; the script will refuse.
- Identify the relevant `/sdlc-kit:trd` record(s) — NFRs cited in the API
  spec must be real references, not invented numbers.

### 2. Scaffold
Run `scripts/api.py --action scaffold` with:
- `--kind {rest|async|grpc|webhook}`
- `--slug <slug>` (**always required**)
- `--title "<human title>"` (**required**)
- `--owner <handle>` (optional; falls back to marker.json owner)

The script:
- validates the slug against `[a-z0-9][a-z0-9-]*`
- refuses to overwrite unless `--force` is passed
- substitutes `{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`,
  `{{PROJECT_NAME}}` in the template
- emits a JSON report with the final path

### 3. Interview
Walk the user through the template. Fill every section via Edit/Write using
the user's chat language. Per-kind priorities:

| Kind      | Must-fill sections                                                                                           |
|-----------|---------------------------------------------------------------------------------------------------------------|
| `rest`    | Base URL, auth, every endpoint (verb, path, request + response schema), error codes table, rate limits, OpenAPI block |
| `async`   | Broker, topics/queues, per-topic schema (AsyncAPI), delivery guarantees, ordering, idempotency, DLQ policy    |
| `grpc`    | Proto package, every RPC (unary/streaming), request/response messages, error-code mapping, deadlines, retry   |
| `webhook` | Emitted events, payload schema, HMAC signature scheme, retry policy, replay tooling, integrator best practices |

Every `<placeholder>` / `<Resource>` / `<Event>` token in the template must
become concrete or be explicitly dropped with a 1-line justification.

### 4. Cross-link
- Wikilink the feature spec: `[[<feature>-design]]`.
- Wikilink the backing TRD for NFR citations:
  `[[<feature>-trd]]` — rate limit, latency budget, availability target.
- Wikilink ADRs justifying non-obvious tech choices:
  `[[ADR-NNNN-<slug>]]` (e.g., *why* Kafka over RabbitMQ, *why* gRPC over
  REST for the streaming path).
- For `async`, wikilink the emitting/consuming domain aggregates and events:
  `[[<aggregate-slug>]]`, `[[<event-slug>]]`.
- For `rest`/`grpc` that front a bounded context, wikilink `[[context-map]]`
  and the relevant `[[<aggregate-slug>]]`.

### 5. Decide
Once the contract is complete and both lenses agree:
```
scripts/api.py --action transition --kind <kind> --slug <slug> --to approved
```
Use `--to deprecated` when the contract is replaced by another record; cite
the successor in the deprecated note's body:
`Superseded by [[<new-slug>]] — migration window <start>..<end>.`

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] Every endpoint / topic / RPC / event has a request + response (or
      payload) schema with concrete types — no `<placeholder>` left.
- [ ] Error model is documented with explicit status codes / gRPC codes /
      retry-triggering conditions.
- [ ] Auth model is explicit (Bearer JWT, mTLS + metadata, HMAC signature,
      API key, etc.) and the scope/claim requirements are listed.
- [ ] Versioning policy is stated — URL versioning (`/v1`), header
      versioning, Proto package version (`org.project.v1`), `api_version`
      field in webhook payload, etc.
- [ ] Non-functional constraints are cited from the relevant TRD: rate
      limits, latency budget, quota, availability target. No invented
      numbers — every NFR must wikilink back to the TRD that owns it.
- [ ] Backward-compat policy for breaking changes is documented: how long
      the old version coexists, how deprecation is signalled, how consumers
      are notified.
- [ ] Both lenses (API Designer + Senior Engineer) have reviewed the note
      and explicitly signed off. One-sided approval is not enough.
- [ ] Consumer ergonomics are sane: idempotency keys where applicable,
      pagination for list endpoints, retry guidance for failure modes,
      clock-skew tolerance for HMAC.

## Output contract

All actions emit a single JSON object on stdout. Common fields: `status`,
`action`, `vault_root`, `errors`.

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`,
  `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`,
  `new_status` (equal on idempotent re-runs).

Exit codes: `0` ok/dry-run, `1` user error (invalid kind/slug/status,
missing required arg, target already exists without `--force`), `2` fatal
(template missing, filesystem failure).

## Guardrails

**Never:**
- Delete a `deprecated` API record. History matters for consumer
  coordination — customers integrating yesterday must be able to find the
  migration note tomorrow. The vault is append-only for API contracts.
- Rename an API file — renaming breaks every wikilink pointing at it.
  Scaffold a new record and deprecate the old one instead.
- Promote to `approved` with placeholder tokens (`<resource>`, `<Event>`,
  `<Service>`) still in the body — the contract has to be real.
- Promote to `approved` with NFR numbers (rate limit, latency) that are not
  backed by an explicit TRD citation. No fantasy SLAs.
- Promote to `approved` without **both** lenses signing off. A producer-only
  review misses consumer pain; a consumer-only review misses producer
  constraints.
- Mix two independent APIs into one record — split by domain responsibility,
  not by convenience.

**Always:**
- When deprecating, add a `Superseded by [[<new-slug>]]` note in the body
  and state the coexistence window. Deprecation without a successor pointer
  is a dead end for integrators.
- Keep the `updated` field honest — the `transition` action refreshes it
  automatically.
- Mirror the user's chat language in narrative sections (overview,
  descriptions); keep frontmatter, schema blocks (OpenAPI/AsyncAPI/proto),
  error codes, and HTTP verbs in English.
- Cross-link the feature spec, backing TRD, and relevant ADRs — an isolated
  API note is a broken API note.

## Examples

### Bootstrap a new REST API

```
scripts/api.py --action scaffold --kind rest --slug users-v1 --title "Users API v1"
```
Then interview the user through the endpoints, error model, and OpenAPI
block; cite the TRD for rate limits; cross-link to `[[users-design]]`;
promote to `approved` when both lenses agree.

### New async event contract

```
scripts/api.py --action scaffold --kind async --slug billing-async-v2 --title "Billing Events v2"
```
Define each topic, its schema, ordering guarantees, DLQ, and wikilink the
emitting aggregate and the replaced v1 record.

### New gRPC service

```
scripts/api.py --action scaffold --kind grpc --slug billing-v1 --title "Billing"
```
Fill in every RPC, the proto block, and the error-code mapping; cite the
ADR that chose gRPC over REST for this boundary.

### Outbound webhook for customers

```
scripts/api.py --action scaffold --kind webhook --slug customer-notifications --title "Customer Notifications"
```
Document every emitted event, the HMAC signing scheme, retry/backoff
policy, and integrator best practices.

### Retire a v1 REST API

```
scripts/api.py --action scaffold --kind rest --slug users-v2 --title "Users API v2"
# ... interview, approve ...
scripts/api.py --action transition --kind rest --slug users-v1 --to deprecated
```
Edit the `users-v1` body to add:
`Superseded by [[users-v2]] — coexistence 2026-05-01..2026-11-01.`

### List everything of a given kind

```
scripts/api.py --action list --kind webhook
```

### Smell: approving a contract without a TRD citation

If the user asks to approve a `rest` API whose *Rate limits* section reads
`100 req/min per user` with no wikilink to a TRD, refuse. Ask them to
either cite the TRD that owns the NFR or scaffold/update the TRD first.
Approved APIs must be traceable to their non-functional source of truth.
