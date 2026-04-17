---
title: "C4 Container — {{SYSTEM_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# C4 Level 2: Container — {{SYSTEM_NAME}}

> Detalha os containers (apps, bancos de dados, serviços) que compõem o sistema.

## Diagrama

```
[Web App]  --HTTPS--> [API Gateway] --gRPC--> [Service A]
                                    --gRPC--> [Service B]
[Service A] --SQL--> [PostgreSQL DB]
[Service B] --pub/sub--> [Message Queue]
```

_Substitua pelo diagrama real._

## Containers

| Container | Tecnologia | Descrição | Porta |
|-----------|-----------|-----------|-------|
| Web App | Next.js 15 | Interface do usuário | 3000 |
| API Gateway | Go / chi | Roteamento e autenticação | 8080 |
| Service A | Go | Lógica de domínio A | 8081 |
| PostgreSQL | PostgreSQL 16 | Persistência relacional | 5432 |
| Message Queue | Redis Streams | Mensageria assíncrona | 6379 |

## Comunicação

| De | Para | Protocolo | Autenticação |
|----|------|-----------|-------------|
| Web App | API Gateway | HTTPS/REST | JWT |
| API Gateway | Service A | gRPC | mTLS |
| Service A | PostgreSQL | TCP/SQL | Password |

## Dados Sensíveis

| Container | Dado Sensível | Proteção |
|-----------|--------------|---------|
| PostgreSQL | CPF, email | Encryption at rest |
| API Gateway | JWT secrets | Secrets Manager |

## Referências

- [[c4-context]] — Visão de sistema
- [[c4-component]] — Detalhamento de componentes
- [[_INDEX]]
