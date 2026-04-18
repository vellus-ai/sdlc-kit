---
type: api-rest
title: "REST API — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [architecture, api, rest]
feature: ""
base_url: ""
auth: "Bearer JWT"
---

# REST API — {{TITLE}}

> _(Feature REST contract — endpoints, schemas, auth and error codes.)_

## Overview

Describe in 1 paragraph the domain and resources exposed by the API.

- **Base URL:** `https://api.example.com/v1`
- **Format:** JSON (UTF-8)
- **Authentication:** Bearer JWT in `Authorization` header
- **Versioning:** via path (`/v1`, `/v2`)

## Endpoints

### `POST /v1/<resource>`

Creates a new <resource>.

- **Auth:** required
- **Idempotency:** via `Idempotency-Key` header
- **Rate limit:** 100 req/min per user

**Request body:**

```json
{
  "field_a": "string",
  "field_b": 123
}
```

**Response 201 Created:**

```json
{
  "id": "uuid",
  "field_a": "string",
  "field_b": 123,
  "created_at": "2026-04-17T12:00:00Z"
}
```

### `GET /v1/<resource>/{id}`

Retrieves <resource> by ID.

- **Auth:** required
- **Cache:** `ETag` + `If-None-Match`

**Response 200 OK:** same schema as POST.

### `GET /v1/<resource>?page=N&size=M`

Lists <resources> with pagination.

**Response 200 OK:**

```json
{
  "items": [ { "..." } ],
  "total": 42,
  "page": 1,
  "size": 20
}
```

## OpenAPI (inline)

```yaml
openapi: 3.1.0
info:
  title: {{TITLE}}
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /<resource>:
    post:
      summary: Creates <resource>
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResource'
      responses:
        '201':
          description: Created
components:
  schemas:
    CreateResource:
      type: object
      required: [field_a]
      properties:
        field_a:
          type: string
        field_b:
          type: integer
```

## Error codes

| HTTP | Business code | Meaning |
|---|---|---|
| 400 | `INVALID_PAYLOAD` | Invalid payload |
| 401 | `UNAUTHENTICATED` | Token missing/expired |
| 403 | `FORBIDDEN` | No permission |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Inconsistent state |
| 422 | `VALIDATION_ERROR` | Business rule violated |
| 429 | `RATE_LIMITED` | Rate limit hit |
| 500 | `INTERNAL_ERROR` | Internal error (opaque) |

**Standard error format:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field X is required",
    "trace_id": "abc123"
  }
}
```

## Rate limits

- **Anonymous:** 20 req/min per IP.
- **Authenticated:** 100 req/min per user.
- **Returned headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Examples

```bash
curl -X POST https://api.example.com/v1/<resource> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"field_a": "value"}'
```

## References

- **Feature spec:** [[<feature>-design]]
- [[ADR-NNNN-<slug>]] — versioning decision
- [[_INDEX]] — global index
