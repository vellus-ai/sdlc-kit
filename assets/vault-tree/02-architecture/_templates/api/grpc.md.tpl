---
type: api-grpc
title: "gRPC API — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 02
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [architecture, api, grpc]
feature: ""
proto_package: ""
---

# gRPC API — {{TITLE}}

> _(Feature gRPC contract — service, RPCs, streaming and proto contracts.)_

## Overview

Describe in 1 paragraph the exposed service and its use cases.

- **Proto package:** `<org.project.v1>`
- **Authentication:** <ex: mTLS + metadata JWT>
- **Default deadline:** <ex: 5s>
- **Retry policy:** <ex: up to 3x with exponential backoff on `UNAVAILABLE`>

## Proto contract

```proto
syntax = "proto3";

package org.project.v1;

option go_package = "org/project/v1;projectv1";

service {{TITLE}}Service {
  // Unary: creates a resource.
  rpc Create(CreateRequest) returns (Resource);

  // Server streaming: lists resource events.
  rpc SubscribeEvents(SubscribeRequest) returns (stream Event);

  // Client streaming: chunked upload.
  rpc Upload(stream Chunk) returns (UploadSummary);

  // Bidi streaming: live chat/commands.
  rpc Session(stream Command) returns (stream Response);
}

message CreateRequest {
  string field_a = 1;
  int32  field_b = 2;
}

message Resource {
  string id = 1;
  string field_a = 2;
  int32  field_b = 3;
  google.protobuf.Timestamp created_at = 4;
}

message SubscribeRequest { string resource_id = 1; }
message Event         { string type = 1; bytes payload = 2; }
message Chunk          { bytes data = 1; }
message UploadSummary   { int64 total_bytes = 1; string sha256 = 2; }
message Command        { string type = 1; }
message Response       { string type = 1; }
```

## RPCs

### `Create(CreateRequest) → Resource`

- **Type:** unary
- **Auth:** required
- **Idempotency:** via metadata `idempotency-key`
- **Expected codes:** `OK`, `INVALID_ARGUMENT`, `ALREADY_EXISTS`, `PERMISSION_DENIED`

### `SubscribeEvents(SubscribeRequest) → stream Event`

- **Type:** server streaming
- **Deadline:** not applicable (long-lived)
- **Flow control:** client applies backpressure via gRPC

### `Upload(stream Chunk) → UploadSummary`

- **Type:** client streaming
- **Max size per chunk:** 64 KB
- **Deadline:** 60s

### `Session(stream Command) → stream Response`

- **Type:** bidi streaming
- **Heartbeat:** `ping` every 30s
- **Reconnection:** client must reopen with exponential backoff

## Error codes (mapping)

| gRPC code | Meaning | Example |
|---|---|---|
| `OK` | Success | — |
| `INVALID_ARGUMENT` | Invalid payload | missing field |
| `NOT_FOUND` | Resource doesn't exist | unknown id |
| `ALREADY_EXISTS` | Idempotency conflict | repeated idempotency-key with different body |
| `PERMISSION_DENIED` | No permission | insufficient role |
| `UNAUTHENTICATED` | Token missing/invalid | — |
| `RESOURCE_EXHAUSTED` | Rate limit | too many requests |
| `UNAVAILABLE` | Transient unavailability | retry ok |
| `INTERNAL` | Unexpected error | |

## Observability

- **Mandatory interceptors:** logging, tracing (OpenTelemetry), metrics, auth.
- **Propagated headers:** `trace-id`, `span-id`, `tenant-id`.

## Client examples

```bash
grpcurl -d '{"field_a":"x"}' \
  -H "authorization: Bearer $TOKEN" \
  api.example.com:443 org.project.v1.{{TITLE}}Service/Create
```

## References

- **Feature spec:** [[<feature>-design]]
- [[_INDEX]] — global index
