---
title: "Test Cases — {{FEATURE_NAME}}"
type: test-case
status: draft
phase: "04"
test_plan: "{{TEST_PLAN}}"
created: {{DATE}}
updated: {{DATE}}
---

# Test Cases: {{FEATURE_NAME}}

## TC-001: [Nome do Caso de Teste]

**Tipo:** Unitário | Integração | E2E | Manual
**Prioridade:** Alta | Média | Baixa
**Requisito:** [[requirements#RF-01]]

**Pré-condições:**
- Usuário autenticado com perfil [X]
- [Estado inicial do sistema]

**Passos:**
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]

**Resultado Esperado:**
- O sistema retorna [resposta esperada]
- O estado do banco de dados é [estado esperado]

**Resultado Real:** _Preencher após execução_
**Status:** Não Executado | Passou | Falhou | Bloqueado

---

## TC-002: [Nome do Caso de Teste — Caminho Alternativo]

**Tipo:** Unitário
**Prioridade:** Alta
**Requisito:** [[requirements#RF-01]]

**Pré-condições:**
- ...

**Passos:**
1. ...

**Resultado Esperado:**
- O sistema retorna erro `[código]` com mensagem `"[mensagem]"`

**Resultado Real:** _Preencher após execução_
**Status:** Não Executado | Passou | Falhou | Bloqueado

---

## TC-003: [Nome do Caso de Teste — Edge Case]

**Tipo:** Unitário
**Prioridade:** Média
**Requisito:** [[requirements#RF-02]]

**Pré-condições:**
- Payload com valor nulo/vazio/máximo

**Passos:**
1. ...

**Resultado Esperado:**
- ...

**Resultado Real:** _Preencher após execução_
**Status:** Não Executado | Passou | Falhou | Bloqueado

## Resumo de Execução

| Total | Passou | Falhou | Bloqueado | Não Executado |
|-------|--------|--------|-----------|---------------|
| 3 | 0 | 0 | 0 | 3 |

## Referências

- [[test-plan]] — Plano de teste relacionado
- [[requirements]] — Requisitos testados
- [[_INDEX]]
