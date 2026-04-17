# {{PROJECT_NAME}} — SDLC Vault Doctrine

**Created:** {{DATE}}
**Stack:** {{STACK}}
**Owner:** {{OWNER}}
**Repository:** {{REPO_URL}}

## Regras Não-Negociáveis para o LLM

1. Ler este arquivo ANTES de qualquer escrita no vault
2. Nunca editar este CLAUDE.md (solicitar permissão ao usuário)
3. Toda feature começa com `/sdlc-kit:spec` — SDD obrigatório
4. Todo documento deve ter frontmatter completo (title, type, status, phase)
5. Todo documento deve ter pelo menos 1 wikilink para outro doc do vault
6. Invocar `/sdlc-kit:sync` ao final de qualquer escrita no vault
7. Nenhum arquivo fora das 7 pastas de fase
8. Nomes de arquivo: sem acentos, snake_case

## Mapa de Fases

| Pasta | Conteúdo |
|-------|----------|
| 01-planning/ | PRDs, requisitos, personas |
| 02-architecture/ | ADRs, domínio DDD, C4, design system |
| 03-development/ | Épicos, milestones, tasks, histórias |
| 04-testing/ | Test plans, test cases |
| 05-deployment/ | Runbooks, release checklists, README, CHANGELOG |
| 06-decisions/ | Decisões pontuais não-arquiteturais |
| 07-retrospectives/ | Retros de sprint e fase |

## Frontmatter Obrigatório

```yaml
---
title: "Título do documento"
type: prd | requirements | design | adr | epic | milestone | story | test-plan | runbook | decision | retro
status: draft | in-review | accepted | active | done | archived
phase: "01" | "02" | "03" | "04" | "05" | "06" | "07"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## Stack Tecnológica

{{STACK_DETAILS}}

## Bounded Contexts Ativos

Ver [[context-map]] em `02-architecture/domain/context-map.md`

## Leitura Obrigatória no Início de Cada Sessão

[[_INDEX]] — índice vivo do vault, atualizado pelo sync
