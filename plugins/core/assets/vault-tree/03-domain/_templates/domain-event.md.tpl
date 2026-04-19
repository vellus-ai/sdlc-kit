---
type: domain-event
title: "Event — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 03
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-domain
owner: "{{OWNER}}"
tags: [domain, ddd, event]
context: ""
aggregate: ""
---

# Event — {{TITLE}}

> _(Domain event — immutable fact from the past, in past tense: something that happened.)_

## Metadata

- **Context:** <emitting context>
- **Emitting aggregate:** [[<aggregate-slug>]]
- **Technical topic:** `<org>.<domain>.<event>.v1`
- **Schema version:** `1.0`

## When it is emitted

Precise trigger in the aggregate's lifecycle.

> _Example: "Emitted after successful `<Command>` on aggregate `<Aggregate>`, when the local transaction is committed."_

## Payload

```json
{
  "event_id": "uuid",
  "event_type": "<context>.<event-in-past-tense>",
  "aggregate_id": "uuid",
  "aggregate_type": "<Aggregate>",
  "version": 1,
  "occurred_at": "2026-04-17T12:00:00Z",
  "payload": {
    "field_a": "string",
    "field_b": 123
  }
}
```

### Mandatory fields

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | unique identifier — idempotency |
| `event_type` | string | canonical event name |
| `aggregate_id` | UUID | aggregate identity |
| `aggregate_type` | string | aggregate type |
| `version` | int | event version in aggregate |
| `occurred_at` | ISO-8601 | date/time of fact (not publication) |
| `payload` | object | event-specific data |

## Consumers

| Consumer | Context | Action on consume |
|---|---|---|
| <Service X> | <Context B> | <projection, workflow triggered> |
| <Service Y> | <Context C> | <notification> |

## Ordering and delivery

- **Partitioning:** by `aggregate_id` (events from same aggregate in order).
- **Delivery:** at-least-once — consumers must be idempotent.
- **Expected latency (p95):** <ex: ≤ 1s>.

## Schema evolution

- **Backward-compatible additions:** OK (optional field).
- **Removal or type change:** requires new version `...v2` and coexistence.

## Relationship with other events

- **Caused by:** [[<predecessor-event>]]
- **Causes:** [[<successor-event>]]

## References

- **Async API:** [[<api-async-slug>]]
- [[context-map]] — contexts map
- [[_INDEX]] — global index
