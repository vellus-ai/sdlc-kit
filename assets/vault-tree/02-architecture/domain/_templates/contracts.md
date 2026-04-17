---
title: "Contracts — {{CONTEXT_A}} ↔ {{CONTEXT_B}}"
type: design
status: draft
phase: "02"
upstream: "{{CONTEXT_A}}"
downstream: "{{CONTEXT_B}}"
created: {{DATE}}
updated: {{DATE}}
---

# Contrato: {{CONTEXT_A}} → {{CONTEXT_B}}

> Define o contrato de integração entre bounded contexts.
> O upstream NÃO pode quebrar este contrato sem versionamento.

## Tipo de Integração

- [ ] Events (publish/subscribe)
- [ ] API (request/response)
- [ ] Shared Kernel
- [ ] Open Host Service + Published Language

## Eventos Consumidos

| Evento | Versão | Desde | Obrigatório |
|--------|--------|-------|-------------|
| `{{CONTEXT_A}}.EventoX` | v1 | {{DATE}} | sim |

## Endpoints Consumidos (se API)

| Método | Path | Versão | Descrição |
|--------|------|--------|-----------|
| GET | `/v1/resource` | v1 | ... |

## Anti-Corruption Layer (ACL)

_Descreva as transformações aplicadas ao consumir dados do contexto upstream._

```
Upstream.ConceptoX → Downstream.ConceptoY (via ACL)
Regra: ...
```

## SLA e Disponibilidade

- Disponibilidade esperada do upstream: 99.9%
- Timeout configurado no downstream: 5s
- Estratégia de fallback: ...

## Versionamento

| Versão | Mudanças | Breaking | Data |
|--------|---------|---------|------|
| v1 | Versão inicial | — | {{DATE}} |

## Referências

- [[domain-events]] — Eventos do upstream
- [[context-map]] — Mapa de contextos
- [[_INDEX]]
