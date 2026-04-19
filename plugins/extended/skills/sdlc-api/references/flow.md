# sdlc-kit:api — full flow

## Kinds, paths and templates

| Kind      | Type slug (frontmatter) | Path                                    | Template                            |
|-----------|-------------------------|-----------------------------------------|-------------------------------------|
| `rest`    | `api-rest`              | `02-architecture/api/rest/<slug>.md`    | `_templates/api/rest.md.tpl`        |
| `async`   | `api-async`             | `02-architecture/api/async/<slug>.md`   | `_templates/api/async.md.tpl`       |
| `grpc`    | `api-grpc`              | `02-architecture/api/grpc/<slug>.md`    | `_templates/api/grpc.md.tpl`        |
| `webhook` | `api-webhook`           | `02-architecture/api/webhook/<slug>.md` | `_templates/api/webhook.md.tpl`     |

If an API exists in two styles (e.g., same resource via `rest` + `grpc`), scaffold
two records and cross-link them.

## Lifecycle

```
draft  →  approved  →  deprecated
```

- **`draft`** — scaffolded, under design. Consumers must NOT rely on it.
- **`approved`** — both lenses signed off. Producers guarantee per SLA/versioning.
- **`deprecated`** — superseded or retired. Kept forever. New work must cite the successor.

## Flow

### 1. Pre-flight
- Read the target vault's `CLAUDE.md` — project conventions may override template defaults.
- Run `list` first. **Never scaffold on top of an existing file without `--force`**.
- Identify relevant `/sdlc-kit:trd` records — NFRs cited must be real references.

### 2. Scaffold
Run `scripts/api.py --action scaffold` with:
- `--kind {rest|async|grpc|webhook}`
- `--slug <slug>` (always required; `[a-z0-9][a-z0-9-]*`)
- `--title "<human title>"` (required)
- `--owner <handle>` (optional)

The script validates slug, refuses to overwrite without `--force`, substitutes
`{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`, `{{PROJECT_NAME}}`, and emits
a JSON report.

### 3. Interview

| Kind      | Must-fill sections |
|-----------|--------------------|
| `rest`    | Base URL, auth, every endpoint (verb, path, request + response schema), error codes table, rate limits, OpenAPI block |
| `async`   | Broker, topics/queues, per-topic schema (AsyncAPI), delivery guarantees, ordering, idempotency, DLQ policy |
| `grpc`    | Proto package, every RPC (unary/streaming), request/response messages, error-code mapping, deadlines, retry |
| `webhook` | Emitted events, payload schema, HMAC signature scheme, retry policy, replay tooling, integrator best practices |

Every `<placeholder>` token must become concrete or be explicitly dropped with
a 1-line justification.

### 4. Cross-link
- Wikilink the feature spec: `[[<feature>-design]]`.
- Wikilink the backing TRD for NFR citations: `[[<feature>-trd]]`.
- Wikilink ADRs justifying non-obvious tech choices: `[[ADR-NNNN-<slug>]]`.
- For `async`: wikilink emitting/consuming aggregates and events.
- For `rest`/`grpc` fronting a bounded context: wikilink `[[context-map]]` and relevant `[[<aggregate-slug>]]`.

### 5. Decide
```
scripts/api.py --action transition --kind <kind> --slug <slug> --to approved
```
Use `--to deprecated` when replaced; cite successor in the body:
`Superseded by [[<new-slug>]] — migration window <start>..<end>.`

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] Every endpoint / topic / RPC / event has concrete request + response (or payload) schema — no `<placeholder>` left.
- [ ] Error model documented: status codes / gRPC codes / retry-triggering conditions.
- [ ] Auth model explicit (Bearer JWT, mTLS, HMAC, API key) with scope/claim requirements.
- [ ] Versioning policy stated (URL `/v1`, header, proto package `org.project.v1`, `api_version` field, etc.).
- [ ] Non-functional constraints cited from the relevant TRD — no invented numbers.
- [ ] Backward-compat policy documented: coexistence window, deprecation signalling, consumer notification.
- [ ] Both lenses (API Designer + Senior Engineer) explicitly signed off.
- [ ] Consumer ergonomics sane: idempotency keys, pagination, retry guidance, clock-skew tolerance.

## Output contract

All actions emit a single JSON object on stdout. Common fields: `status`,
`action`, `vault_root`, `errors`.

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`, `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`, `new_status`.

Exit codes: `0` ok/dry-run, `1` user error, `2` fatal.

## Guardrails

**Never:**
- Delete a `deprecated` API record. History matters for consumer coordination.
- Rename an API file — renaming breaks every wikilink. Scaffold new + deprecate old.
- Promote to `approved` with placeholder tokens still in the body.
- Promote to `approved` with NFR numbers not backed by an explicit TRD citation.
- Promote without **both** lenses signing off.
- Mix two independent APIs into one record.

**Always:**
- When deprecating, add `Superseded by [[<new-slug>]]` and state the coexistence window.
- Keep the `updated` field honest — `transition` refreshes it automatically.
- Mirror the user's chat language in narrative; keep frontmatter, schemas, error codes, HTTP verbs in English.
- Cross-link the feature spec, backing TRD, and relevant ADRs.

## Examples

### Bootstrap a new REST API

```
scripts/api.py --action scaffold --kind rest --slug users-v1 --title "Users API v1"
```
Interview endpoints, error model, OpenAPI block; cite TRD for rate limits; cross-link `[[users-design]]`; promote when both lenses agree.

### New async event contract

```
scripts/api.py --action scaffold --kind async --slug billing-async-v2 --title "Billing Events v2"
```
Define each topic, schema, ordering guarantees, DLQ; wikilink emitting aggregate and the v1 replacement.

### New gRPC service

```
scripts/api.py --action scaffold --kind grpc --slug billing-v1 --title "Billing"
```
Fill every RPC, the proto block, error-code mapping; cite the ADR that chose gRPC.

### Outbound webhook

```
scripts/api.py --action scaffold --kind webhook --slug customer-notifications --title "Customer Notifications"
```
Document every emitted event, HMAC signing scheme, retry/backoff, integrator guidance.

### Retire a v1 REST API

```
scripts/api.py --action scaffold --kind rest --slug users-v2 --title "Users API v2"
# ... interview, approve ...
scripts/api.py --action transition --kind rest --slug users-v1 --to deprecated
```
Edit `users-v1` body to add:
`Superseded by [[users-v2]] — coexistence 2026-05-01..2026-11-01.`

### List by kind

```
scripts/api.py --action list --kind webhook
```

### Smell: approving without a TRD citation

If a `rest` API's rate limits section says `100 req/min per user` with no
wikilink to a TRD, refuse. Ask the user to cite the TRD or scaffold/update one first.
