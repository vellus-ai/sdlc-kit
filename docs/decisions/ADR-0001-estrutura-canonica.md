---
id: ADR-0001
title: Estrutura canônica do vault .sdlc/
status: accepted
date: 2026-04-17
author: Milton Silva Jr.
tags: [architecture, vault, scaffold]
---

# ADR-0001 — Estrutura canônica do vault `.sdlc/`

> 🇬🇧 **English summary:** This ADR fixes the canonical layout of the `.sdlc/` vault as **8 numbered top-level directories** (`00-steering`, `01-planning`, `02-architecture`, `03-domain`, `04-specs`, `05-development`, `06-design-system`, `07-retrospectives`), each with deterministic sub-folders. Decided because three competing layouts were circulating and none mapped 1-to-1 to the 21 (now 22) skills. Status: **accepted**.

## Status

Aceita.

## Contexto

O SDLC Kit cria e mantém um vault `.sdlc/` dentro do repositório Git do projeto. Precisamos fixar a hierarquia de pastas antes de refinar as 21 skills, caso contrário cada skill acabaria assumindo convenções distintas e o grafo de wikilinks ficaria inconsistente.

O plano original (`joyful-swimming-origami.md`) apresentava uma estrutura vaga e mutante entre documentos. Três variações circularam:

1. `01-planning, 02-architecture, 03-development, 04-testing, 05-deployment, 06-decisions, 07-retrospectives` (assets/vault-tree atual).
2. `planning, architecture, development, domain, operations, design-system, retrospectives` (SKILL.md do `init`).
3. Estrutura por fase do SDD (Kiro-style).

Nenhuma das três mapeia 1-para-1 com as 21 skills do plugin.

## Decisão

Adotamos 8 diretórios top-level numerados de `00` a `07`, com subpastas determinísticas.

```
.sdlc/
├── CLAUDE.md                     # doutrina (soberana, editável pelo usuário)
├── _INDEX.md                     # índice vivo (regenerado pelo librarian)
├── dashboard.html                # painel autocontido (File System Access API)
├── .sdlc-kit/
│   ├── marker.json               # identifica a raiz do vault
│   ├── db.sqlite                 # eventos, notas, links, tasks, sprints, etc.
│   └── *-errors.log
│
├── 00-steering/                  # visão e princípios (Kiro-style steering docs)
│   ├── product.md                # visão de produto
│   ├── tech.md                   # princípios técnicos
│   └── standards.md              # padrões do time (code style, DoD, commit)
│
├── 01-planning/
│   ├── prd/<slug>.md             # PRDs (iniciativa)
│   ├── epics/<slug>.md           # épicos com seção "## Stories" (bullets)
│   └── milestones/<slug>.md      # marcos com RAG status
│
├── 02-architecture/
│   ├── adr/ADR-<nnnn>-<slug>.md  # numeração automática
│   ├── c4/
│   │   ├── context.md
│   │   ├── container.md
│   │   └── component.md
│   ├── trd/<slug>.md             # Technical Requirements Docs (cross-feature)
│   └── api/                      # criada sob demanda pela skill spec
│       ├── rest/<feature>.md
│       ├── grpc/<feature>.md
│       ├── async/<feature>.md
│       └── webhook/<feature>.md
│
├── 03-domain/
│   ├── context-map.md
│   ├── ubiquitous-language.md
│   ├── aggregates/<nome>.md
│   ├── events/<nome>.md
│   └── contracts/<nome>.md
│
├── 04-specs/
│   └── <feature>/
│       ├── requirements.md       # EARS (testáveis)
│       ├── design.md
│       └── tasks.md              # task list executável
│
├── 05-development/
│   ├── worktrees/<branch>.md
│   └── branches/<branch>.md
│
├── 06-design-system/
│   ├── tokens/<nome>.md
│   ├── components/<nome>.md
│   └── patterns/<nome>.md
│
└── 07-retrospectives/
    ├── retros/<sprint>.md
    ├── reviews/<pr-num>.md
    └── incidents/
        ├── <slug>.md             # incident (status: open/resolved)
        └── <slug>-lessons.md     # lições aprendidas (auto via hook)
```

## Hierarquia conceitual

```
PRD → Epic (com Stories como bullets) → Spec (requirements + design + tasks)
```

- **PRD** (`01-planning/prd/`) descreve a iniciativa de produto.
- **Epic** (`01-planning/epics/`) decompõe o PRD em entregáveis grandes; **stories ficam como bullets dentro do epic**, não como artefato separado.
- **Spec** (`04-specs/<feature>/`) é o trio SDD para uma feature atômica: `requirements.md` (EARS testáveis), `design.md`, `tasks.md`.
- **Milestone** (`01-planning/milestones/`) agrupa épicos por data de entrega.
- **Sprint** (SQLite only, sem pasta) agrupa tasks por ciclo de tempo — registrada e materializada somente em `07-retrospectives/retros/<sprint>.md` ao fechar.

## Fronteira story × requirements

Risco identificado: sobreposição entre *user story* e *requirement*.

| Artefato | Formato | Granularidade | Autor típico | Propósito |
|---|---|---|---|---|
| Story (bullet em epic.md) | "Como X, quero Y, para Z" | Alto nível | Produto | **O QUÊ + PARA QUEM** |
| Requirement (em requirements.md) | "WHEN … THE SYSTEM SHALL …" (EARS) | Atômico, testável | Tech | **COMO TESTAR** |

Uma story pode gerar múltiplas specs; uma spec contém múltiplos requirements; um requirement gera uma ou mais tasks. Essa fronteira deve constar no `CLAUDE.md` do vault.

## Convenções auxiliares

- **Ops/deployment fora do vault**: runbooks, incident response ao vivo e observability ficam onde o time já mantém (Grafana, Runbooks em Notion, etc.). O vault registra apenas *incidents fechados* e *lições aprendidas*.
- **API por subpasta, não por tag**: `02-architecture/api/{rest,grpc,async,webhook}/` criada sob demanda pela skill `spec` quando o usuário define o tipo de API. Tasks de implementação de API devem criar wikilink bidirecional entre a spec em `04-specs/<feature>/` e o contrato em `02-architecture/api/<tipo>/<feature>.md`.
- **Sprint ≠ Milestone**: sprint = ciclo de tempo do time (conceito familiar ao usuário); milestone = marco de produto (data de release).
- **Wikilinks sempre preferidos sobre caminhos relativos** (`[[nome-da-nota]]` em vez de `../01-planning/prd/x.md`).

## Consequências

**Positivas:**
- Grafo de wikilinks consistente entre skills.
- Numeração `00-07` permite extensão futura mantendo ordem visual (ex.: futuro `08-security/` ou `09-compliance/`).
- Retros automáticas pré-populadas a partir de tasks/specs/incidents do período (ver ADR-0003 quando criado).

**Negativas:**
- Reestruturação do `assets/vault-tree/` atual (breaking change interno — plugin ainda em 0.1.0, sem usuários externos).
- Skills que já assumiam caminhos antigos precisam ser revisadas (todas, a partir de `sdlc-init`).

## Decisões rejeitadas

- **Pasta `04-testing/`**: testes vivem junto do código, não no vault. Resultados de QA importantes viram `07-retrospectives/reviews/` ou ADR.
- **Pasta `05-deployment/`**: deploys são registrados no histórico de PRs/CI; o vault não duplica.
- **Story como skill/pasta separada**: economiza 1 skill, 1 pasta, 1 nível de hierarquia. Stories como bullets no epic atendem times pequenos (target do SDLC Kit).
- **`cycle` como nome da skill**: rejeitado em favor de `sprint` — vocabulário mais familiar ao desenvolvedor.

## Ver também

- ADR-0002 — Inventário de skills
