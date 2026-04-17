# SDLC Kit

> Plugin para **Claude Code** que cria e mantém um vault de Spec-Driven Development (SDD) dentro do seu repositório Git — base de conhecimento versionada, Obsidian-compatível, otimizada para LLMs.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-130%20passing-brightgreen?logo=pytest)](https://github.com/vellus-ai/sdlc-kit/actions)
[![Skills](https://img.shields.io/badge/skills-19-blueviolet)](https://github.com/vellus-ai/sdlc-kit/tree/main/skills)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange)](https://github.com/vellus-ai/sdlc-kit/releases/tag/v0.1.0)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?logo=anthropic)](https://claude.ai/code)

---

## O problema que resolve

Ao trabalhar com Claude Code em projetos reais, três problemas surgem constantemente:

- **Decisões arquiteturais se perdem** entre sessões — o LLM não tem contexto do que foi decidido
- **Requisitos ficam fora de sincronia** com a implementação — código avança, spec fica para trás
- **Cada nova sessão começa do zero** — sem histórico de ADRs, épicos, domínio

O SDLC Kit resolve isso criando um vault `.sdlc/` versionado no próprio repositório, com indexação automática, 19 skills de ciclo completo e um dashboard HTML autocontido.

---

## Funcionalidades

- **Vault estruturado** em 7 fases: planning → architecture → development → domain → operations → design-system → retrospectives
- **19 skills** invocáveis via `/sdlc-kit:<nome>` cobrindo o ciclo completo
- **SDD (Spec-Driven Development)** — trio requirements.md (EARS) + design.md + tasks.md por feature
- **DDD** — bounded contexts, ubiquitous language, domain events, context maps, diagramas C4 (Mermaid)
- **Dashboard HTML autocontido** — Kanban, Épicos & Milestones, Documentos, Domínio; sem servidor, via File System Access API
- **Rastreamento de git worktrees** e status de PRs em SQLite
- **Hook automático** PostToolUse que indexa cada `.md` salvo, rate-limited a 1 sinal/5s

---

## Instalação

### Pré-requisitos

| Ferramenta | Versão | Necessário para |
|-----------|--------|----------------|
| Python | 3.11+ | Core e scripts |
| Claude Code CLI | qualquer | Registrar o plugin |
| `git` | qualquer | Skills de worktree |
| `gh` CLI | qualquer | Sync de status de PR (opcional) |
| PyYAML | 6+ | Frontmatter robusto (opcional) |

### 1. Clonar e instalar

```bash
git clone https://github.com/vellus-ai/sdlc-kit.git
cd sdlc-kit

# Instalação mínima
pip install -e .

# Com dependências de dev (para rodar testes)
pip install -e ".[dev]"

# Com PyYAML para frontmatter robusto
pip install -e ".[yaml]"
```

### 2. Registrar o plugin no Claude Code

```bash
claude plugin install /caminho/para/sdlc-kit
```

### 3. Inicializar o banco de dados

```bash
sdlc-kit init-db
```

---

## Uso rápido

Em qualquer projeto Git, abra o Claude Code e execute:

```
/sdlc-kit:init
```

O assistente fará 7 perguntas sobre o projeto e criará o vault `.sdlc/` com toda a estrutura de pastas, templates, `CLAUDE.md`, `_INDEX.md` e `dashboard.html`.

### Fluxo típico de uma feature

```
# 1. Criar spec SDD para a feature
/sdlc-kit:spec "Login com Google"
→ Gera: 03-development/login-com-google/requirements.md (EARS)
         03-development/login-com-google/design.md
         03-development/login-com-google/tasks.md

# 2. Criar épico e vincular ao milestone
/sdlc-kit:epic --epic-name "Autenticação" --milestone "v1.0"
/sdlc-kit:milestone --milestone-name "v1.0" --target-date "2026-06-01"

# 3. Trabalhar em worktree isolado
/sdlc-kit:worktree --action create --branch feat/login-google

# 4. Revisar completude antes do PR
/sdlc-kit:review

# 5. Retrospectiva ao fechar o ciclo
/sdlc-kit:retro --action create --sprint "Sprint 1"
```

---

## Skills disponíveis

### Fundação

| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:init` | Scaffold do vault com entrevista de 7 perguntas (idempotente) |
| `/sdlc-kit:sync` | Valida frontmatter, regenera MOCs e `_INDEX.md`, reporta anomalias |
| `/sdlc-kit:status` | Resumo JSON de saúde do vault (notas, eventos, worktrees) |
| `/sdlc-kit:steer` | Atualiza seções específicas do `CLAUDE.md` do vault de forma segura |

### SDD — Spec-Driven Development

| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:spec` | Trio SDD: `requirements.md` (EARS) + `design.md` + `tasks.md` |
| `/sdlc-kit:prd` | Product Requirements Document em `01-planning/` |
| `/sdlc-kit:adr` | Architecture Decision Record com numeração automática (ADR-NNN) |
| `/sdlc-kit:doc` | Documento genérico a partir de template configurável |

### Entrega

| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:epic` | Cria e lista épicos em `EPICS.md` (append-only) |
| `/sdlc-kit:milestone` | Milestones com RAG status calculado (🔴 Red / 🟡 Amber / 🟢 Green) |
| `/sdlc-kit:task` | Adiciona, lista e atualiza tarefas; suporte a `[EPIC]` e `@branch` |
| `/sdlc-kit:review` | Checklist: spec trios, frontmatter, TASKS.md, ADRs não travados |

### Arquitetura — baseada em DDD

| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:domain` | Bounded context: `context-map.md` + `ubiquitous-language.md` + `domain-events.md` |
| `/sdlc-kit:c4` | Diagramas C4 em Mermaid: Context (`C4Context`), Container, Component |
| `/sdlc-kit:design-system` | Documenta tokens de design, componentes e padrões |
| `/sdlc-kit:trace` | Matriz de rastreabilidade: requisitos EARS → tasks de implementação |
| `/sdlc-kit:impact` | Análise de impacto: busca um conceito/termo em todos os arquivos do vault |

### Ciclo Completo

| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:worktree` | Ciclo completo de git worktrees: `create` / `list` / `close` / `sync` |
| `/sdlc-kit:retro` | Cria retrospectivas e rastreia itens de ação dentro de seções |

---

## Dashboard

Após o `/sdlc-kit:init`, abra `.sdlc/dashboard.html` diretamente no browser (Chrome/Edge recomendado):

1. Clique em **Abrir Vault** → selecione a pasta `.sdlc/` do projeto
2. Permissão concedida uma vez; handle salvo no IndexedDB para sessões futuras

**4 abas disponíveis:**

| Aba | Funcionalidade |
|-----|---------------|
| **Tasks** | Kanban Backlog / Em Progresso / Concluído + Branch Graph com badges de PR |
| **Épicos & Milestones** | Cards com barra de progresso e indicador RAG por milestone |
| **Documentos** | Sidebar de arquivos, render markdown com wikilinks navegáveis |
| **Domínio** | Placeholder para bounded contexts (fase de expansão) |

---

## Estrutura do vault

```
.sdlc/
├── CLAUDE.md                    # Doutrina do vault — lida pelo agente antes de escrever
├── _INDEX.md                    # Índice vivo, regenerado pelo /sdlc-kit:sync
├── dashboard.html               # Dashboard autocontido
├── .sdlc-kit/
│   ├── marker.json              # Identifica a raiz do vault e versão do kit
│   └── db.sqlite                # SQLite: notes, tasks, worktrees, events...
├── 01-planning/                 # PRDs, requirements de alto nível
│   └── _templates/
├── 02-architecture/             # ADRs, diagramas C4, tech design, API design
│   ├── ADR/
│   └── _templates/
├── 03-development/              # Specs SDD, TASKS.md, EPICS.md, MILESTONES.md
│   └── _templates/
├── 04-domain/                   # Bounded contexts, ubiquitous language, domain events
│   └── _templates/
├── 05-operations/               # Runbooks, alertas, on-call
│   └── _templates/
├── 06-design-system/            # Tokens, componentes, padrões
│   └── _templates/
└── 07-retrospectives/           # Retros por sprint/ciclo
    └── _templates/
```

---

## Arquitetura do plugin

```
sdlc-kit/
├── .claude-plugin/
│   └── plugin.json          # Manifest: hook + 19 skills
├── core/                    # Biblioteca Python (stdlib-only)
│   ├── paths.py             # Descoberta do vault por ancestrais
│   ├── db.py                # SQLite + migrations idempotentes (WAL mode)
│   ├── scanner.py           # Delta scan por mtime
│   ├── parser.py            # Frontmatter YAML + wikilinks [[...]]
│   ├── git.py               # git worktree list + gh pr list → SQLite
│   ├── cli.py               # Ponto de entrada: init-db, scan, status
│   └── migrations/
│       └── 001_initial.sql  # 7 tabelas
├── hooks/
│   └── post-vault-write.py  # PostToolUse hook, rate-limited
├── skills/
│   └── sdlc-<nome>/
│       ├── SKILL.md         # Contrato da skill: quando usar, fluxo, guardrails
│       └── scripts/*.py     # Sempre suportam --dry-run; emitem JSON; exit 0/1/2
├── assets/
│   └── vault-tree/          # Templates + dashboard.html
└── tests/                   # 130 testes (pytest)
```

---

## CLI

```bash
sdlc-kit init-db     # Cria o banco SQLite com as 7 tabelas
sdlc-kit scan        # Varredura delta incremental do vault
sdlc-kit status      # Resumo JSON do vault (notas, fases, worktrees)
```

---

## Desenvolvimento

```bash
# Clonar e instalar em modo editável com dev deps
git clone https://github.com/vellus-ai/sdlc-kit.git
cd sdlc-kit
pip install -e ".[dev,yaml]"

# Rodar todos os testes
pytest

# Rodar testes com cobertura
pytest --cov=core --cov-report=html

# Rodar apenas testes rápidos (sem modelos ML)
pytest -m "not slow"
```

### Convenções

- Branch: `feat/<slug>` ou `fix/<slug>`
- TDD: escrever teste antes da implementação
- Scripts em `skills/` sempre com `--dry-run` e saída JSON
- Cobertura mínima: 90% nos módulos `core/`

### Estrutura de uma skill

Cada skill segue o mesmo contrato:

```
skills/sdlc-<nome>/
├── SKILL.md          # Quando invocar, fluxo, guardrails
└── scripts/
    └── <nome>.py     # --dry-run obrigatório; JSON stdout; exit 0/1/2
```

---

## Contribuição

1. Fork o repositório
2. Crie uma branch: `feat/<slug>`
3. Implemente com TDD (teste antes do código)
4. Abra PR descrevendo **o quê** e **por quê**

Para reportar bugs ou sugerir features: [abra uma issue](https://github.com/vellus-ai/sdlc-kit/issues).

---

## Licença

[MIT](LICENSE) © 2026 [Vellus AI](https://github.com/vellus-ai)
