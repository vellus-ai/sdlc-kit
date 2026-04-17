---
title: "Test Plan — {{FEATURE_NAME}}"
type: test-plan
status: draft
phase: "04"
epic: "{{EPIC}}"
created: {{DATE}}
updated: {{DATE}}
---

# Test Plan: {{FEATURE_NAME}}

## Escopo

_O que está dentro e fora do escopo deste plano de teste._

**Em escopo:**
- ...

**Fora de escopo:**
- ...

## Objetivos

- Validar que [comportamento esperado] funciona conforme especificado
- Garantir que não há regressões em [área relacionada]

## Estratégia

| Tipo de Teste | Ferramenta | Cobertura Alvo | Responsável |
|---------------|-----------|----------------|-------------|
| Unitário | pytest / Jest | ≥ 90% | Dev |
| Integração | pytest / Supertest | Caminhos críticos | Dev |
| E2E | Playwright / Cypress | Happy paths | QA |
| Performance | k6 / Locust | SLA definido | DevOps |
| Segurança | OWASP ZAP / Semgrep | OWASP Top 10 | AppSec |

## Casos de Teste

Ver [[test-case]] — arquivo(s) de casos de teste detalhados.

## Ambientes

| Ambiente | URL | Dados | Responsável |
|----------|-----|-------|-------------|
| Dev | localhost | Seed fake | Dev |
| Staging | staging.example.com | Anonymized | QA |

## Critérios de Entrada

- [ ] Feature branch criada e buildando sem erros
- [ ] Requisitos documentados em [[requirements]]
- [ ] Ambiente de teste disponível

## Critérios de Saída

- [ ] Todos os casos de teste executados
- [ ] Zero bugs críticos abertos
- [ ] Cobertura de código atingida
- [ ] Performance dentro do SLA

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| ... | ... | ... | ... |

## Referências

- [[requirements]] — Requisitos testados
- [[_INDEX]]
