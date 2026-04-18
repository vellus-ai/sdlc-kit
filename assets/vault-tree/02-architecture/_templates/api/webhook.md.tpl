---
type: api-webhook
title: "Webhooks — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [architecture, api, webhook]
feature: ""
---

# Webhooks — {{TITLE}}

> _(Webhook contract emitted — events, payload, HMAC signature and retry policy.)_

## Overview

Describe in 1 paragraph which events the system emits via webhook and the target audience (integrators, partners).

- **Transport:** HTTPS POST
- **Format:** JSON (UTF-8)
- **Signature:** HMAC-SHA256 in `X-Signature` header
- **Source:** egress gateway IPs (<list or documentation route>)

## Emitted events

| Event | When it occurs | Idempotency |
|---|---|---|
| `resource.created` | after successful creation | `event_id` (UUID) |
| `resource.updated` | at each relevant change | `event_id` + `version` |
| `resource.deleted` | after deletion | `event_id` |

## Payload

```json
{
  "event_id": "7b3f...",
  "event_type": "resource.created",
  "api_version": "2026-04-17",
  "occurred_at": "2026-04-17T12:00:00Z",
  "delivery_attempt": 1,
  "data": {
    "id": "uuid",
    "field_a": "string",
    "field_b": 123
  }
}
```

## HMAC signature

The receiver must validate the signature before processing.

**Calculation (sender side):**

```
signature = hex( HMAC_SHA256( secret, timestamp + "." + body ) )
```

**Sent headers:**

- `X-Signature: t=<timestamp>,v1=<hex>`
- `X-Event-Id: <uuid>`
- `X-Delivery-Attempt: <N>`

**Validation (receiver side):**

1. Extract `t` and `v1` from header.
2. Reject if `|now - t| > 5min` (guards against replay).
3. Recalculate HMAC and compare in constant time.
4. If valid, process; if duplicate (`event_id` already seen), respond `200 OK` without reprocessing.

## Retry policy

- **Success response:** `2xx` within 10s.
- **Retry on:** timeout, `5xx`, network error.
- **Backoff:** exponential with jitter — 1min, 5min, 30min, 2h, 12h, 24h.
- **Give up after:** 6 attempts or 48h, whichever comes first.
- **Final delivery failure:** marked in integrator UI + event available for manual replay.

## Test endpoints

- **Sandbox:** `https://webhooks-sandbox.example.com` (simulated events).
- **Inspector:** UI to inspect attempts, payloads and retries.
- **Replay:** admin endpoint to resend event by `event_id`.

## Best practices for the integrator

- Respond fast (`200 OK`) and process in background.
- Treat webhooks as events, not commands: order is not guaranteed (use `occurred_at` + `version`).
- Implement idempotency based on `event_id`.
- Monitor `X-Delivery-Attempt` > 1 as a sign of instability.

## References

- **Feature spec:** [[<feature>-design]]
- [[_INDEX]] — global index
