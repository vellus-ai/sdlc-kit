---
type: api-async
title: "Async API — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [architecture, api, async, events]
feature: ""
broker: ""
---

# Async API — {{TITLE}}

> _(Messaging/events contract — topics, schemas, ordering, idempotency and DLQ.)_

## Overview

Describe in 1 paragraph the domain of events and the publish/consume flows.

- **Broker:** <Kafka / RabbitMQ / Google Pub/Sub / AWS SNS+SQS>
- **Protocol:** <AMQP 0.9.1 / Kafka wire / etc.>
- **Payload format:** <JSON / Avro / Protobuf>
- **Schema registry:** <URL, if any>

## Topics / Queues

| Topic | Type | Producer | Consumers | Ordering |
|---|---|---|---|---|
| `<org>.<domain>.<event>.v1` | pub/sub | <service A> | <service B, C> | by `aggregate_id` |
| `<org>.<domain>.<command>.v1` | command | <service X> | <service Y> | FIFO |

## Schema (AsyncAPI inline)

```yaml
asyncapi: 3.0.0
info:
  title: {{TITLE}}
  version: 1.0.0
servers:
  broker:
    host: broker.example.com:9092
    protocol: kafka
channels:
  resourceCreated:
    address: 'org.project.resource.created.v1'
    messages:
      ResourceCreated:
        payload:
          type: object
          required: [event_id, aggregate_id, occurred_at, payload]
          properties:
            event_id:     { type: string, format: uuid }
            aggregate_id: { type: string, format: uuid }
            occurred_at:  { type: string, format: date-time }
            version:      { type: integer }
            payload:
              type: object
              properties:
                field_a: { type: string }
                field_b: { type: integer }
operations:
  publish:
    action: send
    channel:
      $ref: '#/channels/resourceCreated'
```

## Guarantees

- **Delivery:** <at-least-once / exactly-once / at-most-once>.
- **Ordering:** <by partition key (`aggregate_id`) / global>.
- **Retention:** <7d / 30d / compacted>.

## Idempotency

Consumers must tolerate redelivery. Strategy:

- Idempotent key: `event_id` (UUID v4 generated at publish).
- Consumer maintains `processed_events(event_id)` table/index with TTL.
- Duplicate processing must be no-op (deterministic result).

## Dead Letter Queue (DLQ)

- **DLQ:** `<topic>.dlq`
- **Trigger:** after N attempts (ex: 5) with exponential backoff.
- **Format:** original message + metadata (`error`, `attempts`, `last_error_at`).
- **DLQ retention:** 14 days.
- **Reprocessing:** manual via operations skill.

## Versioning

- Compatible evolution via optional field addition.
- Breaking change requires new topic `...v2` and coexistence window.

## Observability

- **Metrics:** lag per consumer group, DLQ rate, end-to-end latency.
- **Tracing:** `traceparent` propagated in message header.

## Examples

**Publish (Kafka + JSON):**

```bash
kafka-console-producer --bootstrap-server broker:9092 \
  --topic org.project.resource.created.v1 \
  --property "parse.key=true" --property "key.separator=:" \
  <<< "$AGG_ID:$(cat event.json)"
```

## References

- **Feature spec:** [[<feature>-design]]
- **Domain events:** [[<event-slug>]]
- [[_INDEX]] — global index
