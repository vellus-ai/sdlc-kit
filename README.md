# SDLC Kit

Plugin para Claude Code que cria e mantém um vault de **Spec-Driven Development (SDD)** dentro do seu repositório Git — base de conhecimento versionada, Obsidian-compatível, otimizada para LLMs.

## O que é

O SDLC Kit cria uma pasta `.sdlc/` no seu projeto com:

- **Vault estruturado** em 7 fases (planning → architecture → development → domain → operations → design-system → retrospectives)
- **19 skills** cobrindo o ciclo completo de desenvolvimento
- **Dashboard HTML** autocontido (sem servidor) com Kanban, Épicos, Documentos e Domínio
- **Rastreamento de worktrees** e status de PRs via SQLite
- **Hook automático** que indexa cada arquivo `.md` salvo

## Instalação

### Pré-requisitos

- Python 3.11+
- Claude Code CLI

### 1. Instalar o pacote Python

```bash
cd /caminho/para/sdlc-kit
pip install -e .
# Com dependências de dev (testes):
pip install -e ".[dev]"
# Com suporte a YAML (frontmatter robusto):
pip install -e ".[yaml]"
```

### 2. Registrar o plugin no Claude Code

```bash
claude plugin install /caminho/para/sdlc-kit
```

Ou, se estiver usando o plugin localmente via path:

```bash
claude plugin install C:\workspace\plugin\sdlc-kit
```

### 3. Inicializar o banco de dados

```bash
sdlc-kit init-db
```

## Uso rápido

Em qualquer projeto Git, abra o Claude Code e execute:

```
/sdlc-kit:init
```

O assistente fará 7 perguntas e criará o vault `.sdlc/` com toda a estrutura.

## Skills disponíveis

### Fundação
| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:init` | Scaffold do vault (entrevista 7 perguntas, idempotente) |
| `/sdlc-kit:sync` | Valida frontmatter, atualiza MOCs e `_INDEX.md` |
| `/sdlc-kit:status` | Resumo de saúde do vault em JSON |
| `/sdlc-kit:steer` | Atualiza seções do `CLAUDE.md` do vault |

### SDD (Spec-Driven Development)
| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:spec` | Cria trio requirements.md + design.md + tasks.md (EARS) |
| `/sdlc-kit:prd` | Cria Product Requirements Document |
| `/sdlc-kit:adr` | Cria Architecture Decision Record (numeração automática) |
| `/sdlc-kit:doc` | Cria documento genérico a partir de template |

### Entrega
| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:epic` | Cria e lista épicos em `EPICS.md` |
| `/sdlc-kit:milestone` | Cria milestones com RAG status (Red/Amber/Green) |
| `/sdlc-kit:task` | Adiciona, lista e atualiza tarefas em `TASKS.md` |
| `/sdlc-kit:review` | Verifica completude: spec trios, frontmatter, ADRs |

### DDD + Arquitetura
| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:domain` | Cria bounded context (context-map + ubiquitous-language) |
| `/sdlc-kit:c4` | Gera diagramas C4 em Mermaid (Context/Container/Component) |
| `/sdlc-kit:design-system` | Documenta tokens, componentes e padrões |
| `/sdlc-kit:trace` | Gera matriz de rastreabilidade (requirements → tasks) |
| `/sdlc-kit:impact` | Analisa impacto de mudança de conceito no vault |

### Ciclo Completo
| Skill | Descrição |
|-------|-----------|
| `/sdlc-kit:worktree` | Ciclo completo de git worktrees (create/list/close/sync) |
| `/sdlc-kit:retro` | Cria retrospectivas e gerencia itens de ação |

## CLI

```bash
sdlc-kit init-db     # Inicializa SQLite (7 tabelas)
sdlc-kit scan        # Varredura incremental do vault
sdlc-kit status      # Resumo JSON do vault
```

## Dashboard

Após o init, abra `.sdlc/dashboard.html` no browser:

1. Clique em **Abrir Vault**
2. Selecione a pasta `.sdlc/` do seu projeto
3. 4 abas disponíveis: **Tasks** (Kanban), **Épicos & Milestones**, **Documentos**, **Domínio**

O acesso é persistido via IndexedDB — basta um clique nas próximas sessões.

## Estrutura do vault

```
.sdlc/
├── CLAUDE.md              # Doutrina do vault (lida pelo agente antes de escrever)
├── _INDEX.md              # Índice vivo (atualizado pelo sync)
├── dashboard.html         # Dashboard autocontido
├── .sdlc-kit/
│   ├── marker.json        # Identifica raiz do vault
│   └── db.sqlite          # Banco SQLite (worktrees, tasks, events...)
├── 01-planning/           # PRDs, requirements
├── 02-architecture/       # ADRs, diagramas C4, tech design
├── 03-development/        # Specs (SDD trios), TASKS.md, EPICS.md, MILESTONES.md
├── 04-domain/             # Bounded contexts, ubiquitous language, domain events
├── 05-operations/         # Runbooks, alertas
├── 06-design-system/      # Tokens, componentes, padrões
└── 07-retrospectives/     # Retros
```

## Testes

```bash
pytest                          # Todos os testes (130)
pytest -m "not slow"            # Sem testes lentos
pytest --cov=core               # Com cobertura
```

## Requisitos

- Python 3.11+
- `pyyaml` (opcional, melhora parsing de frontmatter)
- `git` (para skills de worktree)
- `gh` CLI (opcional, para sincronização de PRs)
