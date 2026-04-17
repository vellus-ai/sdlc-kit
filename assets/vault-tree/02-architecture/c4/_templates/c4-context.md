---
title: "C4 Context — {{SYSTEM_NAME}}"
type: design
status: draft
phase: "02"
created: {{DATE}}
updated: {{DATE}}
---

# C4 Level 1: System Context — {{SYSTEM_NAME}}

> Visão de alto nível: o sistema e suas relações com usuários e sistemas externos.

## Diagrama

```
[Usuário Final] --uses--> [{{SYSTEM_NAME}}] --calls--> [Sistema Externo A]
                                              --sends email via--> [SendGrid]
                                              --persists to--> [Database]
```

_Substitua pelo diagrama C4 real (PlantUML, Mermaid, ou imagem)._

## Atores

| Ator | Tipo | Descrição | Interação |
|------|------|-----------|-----------|
| Usuário Final | Person | ... | Usa a interface web |
| Admin | Person | ... | Gerencia configurações |

## Sistemas Externos

| Sistema | Tipo | Descrição | Relação |
|---------|------|-----------|---------|
| [Sistema A] | External Software | ... | Downstream — consome nossa API |
| [SendGrid] | External Software | Envio de email | Upstream — chamamos para notificações |

## {{SYSTEM_NAME}} — Responsabilidades

_O que este sistema faz (e o que NÃO faz)._

**Faz:**
- ...

**Não faz (fora de escopo):**
- ...

## Referências

- [[c4-container]] — Detalhamento dos containers
- [[context-map]] — Bounded contexts internos
- [[_INDEX]]
