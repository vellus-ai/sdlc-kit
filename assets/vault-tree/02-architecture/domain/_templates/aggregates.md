---
title: "Aggregates — {{CONTEXT_NAME}}"
type: design
status: draft
phase: "02"
context: "{{CONTEXT_NAME}}"
created: {{DATE}}
updated: {{DATE}}
---

# Agregados: {{CONTEXT_NAME}}

> Clusters de entidades e value objects tratados como unidade de consistência transacional.

## Aggregate: [NomeAgregado]

**Aggregate Root:** `[EntidadeRaiz]`
**Invariantes:**
- O sistema garante que [invariante 1].
- O sistema garante que [invariante 2].

### Entidades

| Entidade | Descrição | Identificador |
|----------|-----------|---------------|
| `[EntidadeRaiz]` | ... | `id: UUID` |
| `[SubEntidade]` | ... | `id: UUID` |

### Value Objects

| Value Object | Descrição | Imutável |
|-------------|-----------|---------|
| `[ValueObj]` | ... | sim |

### Comandos

| Comando | Pré-condições | Eventos Emitidos |
|---------|--------------|-----------------|
| `Criar[Agregado]` | ... | `[Agregado]Criado` |
| `Atualizar[Campo]` | ... | `[Campo]Atualizado` |

### Regras de Negócio

1. **RN-01:** _Descreva a regra._
2. **RN-02:** _Descreva a regra._

---

## Aggregate: [OutroAgregado]

_Repita a estrutura acima para cada agregado do contexto._

## Referências

- [[ubiquitous-language]] — Terminologia usada
- [[domain-events]] — Eventos emitidos pelos agregados
- [[context-map]] — Contexto delimitado
- [[_INDEX]]
