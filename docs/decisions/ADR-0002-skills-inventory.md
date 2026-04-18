---
id: ADR-0002
title: Inventário de skills do SDLC Kit
status: accepted
date: 2026-04-17
author: Milton Silva Jr.
tags: [skills, inventory]
supersedes: []
---

# ADR-0002 — Inventário de skills do SDLC Kit

## Status

Aceita. Substitui a lista informal em `plugin.json` e no plano `joyful-swimming-origami.md`.

## Contexto

O plano original listava 20 skills. Durante o refinamento decidimos:

- **Adicionar** `incident` (ciclo: open → resolved → lessons, com hook automático).
- **Adicionar** `sprint` (ciclo de tempo com retro automática ao fechar).
- **Cortar** `story` — tratadas como bullets dentro de `epic.md`.
- **Renomear** `tech-design` → `trd`.

Total final: **21 skills**.

## Decisão

### Skills e mapa skill → pasta

| # | Skill | Artefato / Pasta-alvo |
|---|---|---|
| **Bootstrap e saúde** | | |
| 1 | `init` | cria todo o vault |
| 2 | `sync` | reindexação + regenera `_INDEX.md` |
| 3 | `status` | relatório (sem artefato) |
| 4 | `dash` | abre `dashboard.html` |
| **Direção** | | |
| 5 | `steer` | `00-steering/{product,tech,standards}.md` |
| **Planejamento** | | |
| 6 | `prd` | `01-planning/prd/<slug>.md` |
| 7 | `epic` | `01-planning/epics/<slug>.md` (stories como bullets) |
| 8 | `milestone` | `01-planning/milestones/<slug>.md` |
| **Arquitetura** | | |
| 9 | `adr` | `02-architecture/adr/ADR-<nnnn>-<slug>.md` |
| 10 | `c4` | `02-architecture/c4/{context,container,component}.md` |
| 11 | `trd` | `02-architecture/trd/<slug>.md` |
| **Domínio** | | |
| 12 | `domain` | `03-domain/…` |
| **SDD core** | | |
| 13 | `spec` | `04-specs/<feature>/{requirements,design,tasks}.md` |
| 14 | `task` | manipula `04-specs/<feature>/tasks.md` |
| **Entrega** | | |
| 15 | `sprint` | SQLite + `07-retrospectives/retros/<sprint>.md` ao fechar |
| 16 | `worktree` | `05-development/worktrees/<branch>.md` + SQLite |
| **Design System** | | |
| 17 | `design-system` | `06-design-system/{tokens,components,patterns}/` |
| **Retrospectiva** | | |
| 18 | `retro` | `07-retrospectives/retros/<slug>.md` |
| 19 | `review` | `07-retrospectives/reviews/<slug>.md` |
| 20 | `incident` | `07-retrospectives/incidents/<slug>.md` + `<slug>-lessons.md` (hook auto) |
| **Análise cross-vault** | | |
| 21 | `trace` | sem artefato (varre vault) |
| + | `impact` | sem artefato (análise de ripple) |
| + | `doc` | notas soltas (glossário, READMEs) |

> Observação: `impact` e `doc` contam como skills nº 22 e 23 se formos estritos — mas são utilitárias, sem ciclo próprio. Convenção: **21 skills de domínio** + `impact`/`doc` como utilitários. Na prática, o diretório `skills/` terá 23 entradas.

### Comandos e subcomandos

**Invocação:** `/sdlc-kit:<skill> [subcomando] [args]` — Claude Code roteia para `skills/sdlc-<skill>/SKILL.md`.

**Verbos padrão:** `new | list | update | approve | close | status`

**Bootstrap:**
- `/sdlc-kit:init` — entrevista + scaffold (sem subcomandos)
- `/sdlc-kit:sync [--full | --index]`
- `/sdlc-kit:status [--phase <n> | --json]`
- `/sdlc-kit:dash`

**Direção:**
- `/sdlc-kit:steer {product | tech | standards}`

**Planejamento:**
- `/sdlc-kit:prd {new <título> | list | update <slug> | approve <slug>}`
- `/sdlc-kit:epic {new <título> | list | close <slug>}` *(stories ficam como bullets em `## Stories` dentro do epic.md)*
- `/sdlc-kit:milestone {new <título> | status | close <slug>}`

**Arquitetura:**
- `/sdlc-kit:adr {new <título> | supersede <num> | list}`
- `/sdlc-kit:c4 {context | container | component}`
- `/sdlc-kit:trd {new <título> | list}`

**Domínio:**
- `/sdlc-kit:domain {event-storm | context-map | aggregate <nome> | event <nome> | language <termo>}`

**SDD core:**
- `/sdlc-kit:spec {new <feature> | requirements <feature> | design <feature> | tasks <feature> | approve <feature>}`
- `/sdlc-kit:spec api {rest | grpc | async | webhook} <feature>` — cria contrato em `02-architecture/api/<tipo>/<feature>.md`; task de implementação gera o wikilink bidirecional
- `/sdlc-kit:task {add <feature> | complete <feature> <id> | list <feature>}`

**Entrega:**
- `/sdlc-kit:retro {new <sprint> | from-sprint <sprint> | from-incidents <período>}` — artefato de sprint/retrospectiva
- `/sdlc-kit:worktree {new <feature> | list | close <branch> | sync-pr}`

**Design System:**
- `/sdlc-kit:design-system {token <nome> | component <nome> | pattern <nome>}`

**Retrospectiva:**
- `/sdlc-kit:retro {new <sprint> | from-sprint <sprint> | from-incidents <período>}`
- `/sdlc-kit:review {pr <num> | post-impl <feature> | list}`
- `/sdlc-kit:incident {new <título> | resolve <slug> | lessons <slug>}` *(`lessons` é chamado automaticamente pelo hook quando `status: resolved`)*

**Análise:**
- `/sdlc-kit:trace {<termo> | spec <feature> | adr <num>}`
- `/sdlc-kit:impact {<arquivo> | spec <feature> | adr <num>}`
- `/sdlc-kit:doc {new <título> | glossary | readme}`

## Contratos compartilhados

Todas as skills seguem:

- `SKILL.md` com frontmatter `name: sdlc-<nome>` (bare, sem prefixo de plugin) + `description` longa em português.
- `scripts/*.py` com suporte a `--dry-run`; saída JSON estruturada no stdout; exit codes `0/1/2`.
- Erros em `.sdlc-kit/<skill>-errors.log`; não travam a operação principal.
- **Doutrina soberana**: antes de qualquer escrita em nota, skill lê `.sdlc/CLAUDE.md` e respeita schema de frontmatter, hierarquia de tags e voz/tom.
- **Sync obrigatório após escrita**: toda skill que modifica notas dispara `sdlc-kit sync` no final.
- **Nunca editar** `CLAUDE.md` do vault a partir de uma skill.
- **`status: draft`** + `generated_by: sdlc-<nome>` em todo artefato gerado.

## Hook de incidentes (auto-lessons)

Quando o `PostToolUse` hook detecta uma edição em `07-retrospectives/incidents/<slug>.md` que mudou `status` para `resolved`:

1. Grava evento no SQLite.
2. Emite `additionalContext` pedindo ao agente para invocar `sdlc-kit:incident lessons <slug>`.
3. Skill `incident lessons` gera `07-retrospectives/incidents/<slug>-lessons.md` pré-populado com template 5-whys + impacto + mitigação, puxando do SQLite eventos correlatos (commits, PRs, specs afetadas).

## Hook de sprint (auto-retro)

Quando `sdlc-kit:retro` roda ao final do ciclo:

1. Sprint é fechada no SQLite.
2. Script gera `07-retrospectives/retros/<sprint-slug>.md` pré-populado com: tasks fechadas no período, specs entregues, ADRs criadas, incidents abertos/resolvidos, RAG dos milestones.
3. `status: draft` — usuário revisa e aprova.

## Consequências

**Positivas:**
- Fronteira clara entre as 21 skills e 8 pastas.
- Verbos padronizados (`new/list/close/...`) reduzem curva de aprendizado.
- Retros e lições aprendidas saem da inércia — o hook pré-popula, usuário só revisa.

**Negativas:**
- 23 entradas em `skills/` é inventário grande — refinamento individual de cada skill é trabalhoso.
- Documentação de fronteiras (story vs requirement, sprint vs milestone, spec vs PRD) precisa ficar extremamente clara no `CLAUDE.md` do vault, senão usuários se perdem.

## Ver também

- ADR-0001 — Estrutura canônica do vault
