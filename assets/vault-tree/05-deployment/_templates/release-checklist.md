---
title: "Release Checklist — {{VERSION}}"
type: runbook
status: draft
phase: "05"
version: "{{VERSION}}"
release_date: "{{DATE}}"
created: {{DATE}}
updated: {{DATE}}
---

# Release Checklist: {{VERSION}}

**Versão:** {{VERSION}}
**Data planejada:** {{DATE}}
**Responsável:** @[nome]
**Aprovadores:** @[reviewer1], @[reviewer2]

---

## PRÉ-RELEASE

### Código

- [ ] Todos os PRs do milestone mergeados e branch principal verde
- [ ] Nenhum `TODO` ou `FIXME` crítico em produção
- [ ] Dependências auditadas (`npm audit` / `go mod verify`)
- [ ] Changelog atualizado ([[CHANGELOG]])
- [ ] Versão bump realizado (`package.json` / `go.mod` / `pyproject.toml`)

### Testes

- [ ] CI verde em todos os ambientes
- [ ] Testes de regressão executados
- [ ] Performance tests aprovados (SLA dentro do esperado)
- [ ] Testes de segurança executados (SAST, DAST)
- [ ] Smoke tests em staging passando

### Banco de Dados

- [ ] Migrations revisadas e testadas em staging
- [ ] Migrations são backward-compatible (suportam versão N-1)
- [ ] Backup de produção verificado e recente
- [ ] Rollback de migration testado

### Infraestrutura

- [ ] Recursos de infra provisionados (se necessário)
- [ ] Secrets atualizados no gerenciador de segredos
- [ ] Alertas e dashboards configurados
- [ ] Runbook de rollback atualizado ([[runbook]])

### Comunicação

- [ ] Stakeholders notificados (slack / email)
- [ ] Janela de manutenção comunicada (se houver downtime)
- [ ] On-call escalation path definido

---

## DEPLOY

### Execução

- [ ] Backup final antes do deploy
- [ ] Migrations executadas
- [ ] Deploy da nova versão
- [ ] Health check pós-deploy verificado
- [ ] Smoke tests em produção passando

### Monitoramento (primeiros 30 minutos)

- [ ] Error rate normal (< 1%)
- [ ] Latência P99 dentro do SLA
- [ ] CPU e memória normais
- [ ] Sem alertas disparados no observability

---

## PÓS-RELEASE

- [ ] Release notes publicadas no GitHub
- [ ] Stakeholders notificados sobre conclusão
- [ ] Métricas de sucesso sendo rastreadas
- [ ] Retrospectiva agendada (se release complexo)
- [ ] Ticket de "cleanup" aberto (feature flags, código de migração)

---

## ROLLBACK (se necessário)

> Critério de rollback: error rate > 5% por mais de 5 minutos OU indisponibilidade confirmada.

- [ ] Decisão de rollback aprovada por @[responsável]
- [ ] Serviço revertido para versão anterior
- [ ] Migrations revertidas (se aplicável)
- [ ] Stakeholders notificados
- [ ] Post-mortem agendado

**Tempo máximo até decisão de rollback:** 30 minutos após deploy

## Referências

- [[runbook]] — Runbooks operacionais
- [[CHANGELOG]] — Histórico de versões
- [[_INDEX]]
