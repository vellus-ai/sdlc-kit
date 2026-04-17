---
title: "Runbook — {{OPERATION_NAME}}"
type: runbook
status: active
phase: "05"
service: "{{SERVICE_NAME}}"
created: {{DATE}}
updated: {{DATE}}
---

# Runbook: {{OPERATION_NAME}}

**Serviço:** {{SERVICE_NAME}}
**Severidade:** P1 | P2 | P3
**Tempo estimado:** X minutos
**Contato de escalonamento:** @[responsável]

## Descrição

_Quando usar este runbook? Qual problema ele resolve?_

## Pré-requisitos

- [ ] Acesso ao ambiente de produção (SSH / kubectl)
- [ ] Permissão para [ação específica]
- [ ] Backup verificado antes de iniciar

## Diagrama de Decisão (Opcional)

```
Sintoma X detectado
    ↓
Verificar [métrica A]
    ├── Normal → Verificar [métrica B]
    └── Anormal → Executar [Passo 3]
```

## Procedimento

### Passo 1: Verificar Status

```bash
# Verificar saúde do serviço
systemctl status {{SERVICE_NAME}}

# Verificar logs recentes
journalctl -u {{SERVICE_NAME}} --since "10 minutes ago"
```

**Resultado esperado:** `active (running)`

### Passo 2: [Nome da Ação]

```bash
# Comando
echo "exemplo"
```

**Resultado esperado:** _Descreva o que indica sucesso._

### Passo 3: Reiniciar Serviço (se necessário)

```bash
systemctl stop {{SERVICE_NAME}}
systemctl start {{SERVICE_NAME}}
systemctl status {{SERVICE_NAME}}
```

> Tempo de downtime esperado: ~30s

### Passo 4: Validação Pós-Operação

```bash
# Smoke test
curl -sf https://api.example.com/health | jq .
```

**Resultado esperado:** `{"status": "ok"}`

## Rollback

Se a operação falhar, execute:

```bash
# Reverter para versão anterior
systemctl stop {{SERVICE_NAME}}
cp /opt/backups/{{SERVICE_NAME}}.prev /opt/{{SERVICE_NAME}}/binary
systemctl start {{SERVICE_NAME}}
```

## Métricas a Monitorar

| Métrica | Threshold Normal | Ação se Exceder |
|---------|-----------------|-----------------|
| CPU | < 80% | Escalar horizontalmente |
| Memory | < 85% | Investigar leaks |
| Error rate | < 1% | Rollback imediato |
| Latency P99 | < 500ms | Verificar queries lentas |

## Histórico de Incidentes

| Data | Causa | Resolução | Duração |
|------|-------|-----------|---------|
| — | — | — | — |

## Referências

- [[release-checklist]] — Checklist de release
- [[_INDEX]]
