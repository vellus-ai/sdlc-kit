---
title: "C4 Component — {{CONTAINER_NAME}}"
type: design
status: draft
phase: "02"
container: "{{CONTAINER_NAME}}"
created: {{DATE}}
updated: {{DATE}}
---

# C4 Level 3: Component — {{CONTAINER_NAME}}

> Detalha os componentes internos do container `{{CONTAINER_NAME}}`.

## Diagrama

```
[HTTP Handler] --> [Use Case Layer] --> [Domain Service]
                                    --> [Repository Interface]
[Repository Interface] <-- [Repository Impl] --> [Database]
```

_Substitua pelo diagrama real._

## Componentes

| Componente | Padrão | Responsabilidade |
|------------|--------|-----------------|
| HTTP Handler | Adapter (in) | Parse request, valida input, chama use case |
| Use Case | Application | Orquestra fluxo de negócio, sem regras de domínio |
| Domain Service | Domain | Regras de domínio que não pertencem a um agregado |
| Repository Interface | Port (out) | Abstração de persistência |
| Repository Impl | Adapter (out) | Implementação SQL/NoSQL |

## Fluxo Principal: [Nome do Fluxo]

1. HTTP Handler recebe `POST /resource`
2. Valida payload via DTO
3. Chama `UseCaseX.Execute(cmd)`
4. Use Case carrega agregado via Repository
5. Agregado executa lógica de domínio
6. Repository persiste mudanças
7. Use Case publica evento de domínio
8. HTTP Handler retorna `201 Created`

## Dependências Externas do Container

| Componente | Dependência | Tipo |
|------------|-------------|------|
| Repository Impl | PostgreSQL | Database |
| Event Publisher | Redis Streams | Message Broker |

## Referências

- [[c4-container]] — Containers do sistema
- [[aggregates]] — Agregados do domínio
- [[_INDEX]]
