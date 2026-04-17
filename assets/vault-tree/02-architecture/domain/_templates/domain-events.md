---
title: "Domain Events — {{CONTEXT_NAME}}"
type: design
status: draft
phase: "02"
context: "{{CONTEXT_NAME}}"
created: {{DATE}}
updated: {{DATE}}
---

# Eventos de Domínio: {{CONTEXT_NAME}}

> Fatos que ocorreram no domínio e são relevantes para outros contextos ou para auditoria.

## Catálogo de Eventos

### `{{CONTEXT_NAME}}.{{Agregado}}Criado` (v1)

**Descrição:** Emitido quando um novo [Agregado] é criado com sucesso.
**Produtor:** Aggregate `[Agregado]`
**Consumidores:** [Context B], [Context C]

**Payload:**

```json
{
  "event_id": "uuid",
  "event_type": "{{CONTEXT_NAME}}.{{Agregado}}Criado",
  "event_version": "1",
  "occurred_at": "ISO8601",
  "aggregate_id": "uuid",
  "aggregate_type": "{{Agregado}}",
  "data": {
    "id": "uuid",
    "field": "value"
  }
}
```

---

### `{{CONTEXT_NAME}}.{{Agregado}}Atualizado` (v1)

**Descrição:** Emitido quando [campo] de um [Agregado] é alterado.
**Produtor:** Aggregate `[Agregado]`
**Consumidores:** [Context B]

**Payload:**

```json
{
  "event_id": "uuid",
  "event_type": "{{CONTEXT_NAME}}.{{Agregado}}Atualizado",
  "event_version": "1",
  "occurred_at": "ISO8601",
  "aggregate_id": "uuid",
  "aggregate_type": "{{Agregado}}",
  "data": {
    "previous": {},
    "current": {}
  }
}
```

## Política de Retenção

- Eventos de auditoria: 7 anos
- Eventos de integração: 30 dias após consumo confirmado

## Referências

- [[aggregates]] — Agregados que emitem estes eventos
- [[context-map]] — Consumidores por contexto
- [[contracts]] — Contratos de integração
- [[_INDEX]]
