# SDLC Kit

> Plugin para **Claude Code** que cria e mantém um vault de Spec-Driven Development (SDD) e Domain-Driven Design (DDD) dentro do seu repositório Git — base de conhecimento versionada, Obsidian-compatível, otimizada para LLMs.

[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?logo=anthropic)](https://claude.ai/code) [![Skills](https://img.shields.io/badge/skills-23-blueviolet)](https://github.com/vellus-ai/sdlc-kit/tree/main/skills) [![Phases](https://img.shields.io/badge/phases-8-informational)](#estrutura-do-vault) [![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![Version](https://img.shields.io/badge/version-0.3.1-orange)](https://github.com/vellus-ai/sdlc-kit/releases/tag/v0.3.1)

---

## O problema que resolve

Ao trabalhar com Claude Code em projetos reais, três problemas surgem constantemente:

- **Decisões arquiteturais se perdem** entre sessões — o LLM não tem contexto do que foi decidido.
- **Requisitos ficam fora de sincronia** com a implementação — código avança, spec fica para trás.
- **Cada nova sessão começa do zero** — sem histórico de ADRs, épicos, domínio, incidentes.

O SDLC Kit resolve isso criando um vault `.sdlc/` versionado no próprio repositório, com indexação automática, **23 skills** cobrindo o ciclo completo (planning → architecture → domain → specs → development → design-system → retrospectives) e um dashboard HTML autocontido.

---

## Funcionalidades

- **Vault estruturado em 8 fases canônicas** (`00-steering` → `07-retrospectives`).
- **23 skills** invocáveis via `/sdlc-kit:<nome>`, cada uma com contrato `list / scaffold / transition` estável.
- **SDD (Spec-Driven Development)** — trio `requirements.md` (EARS) + `design.md` + `tasks.md` por feature, com portas de aprovação.
- **DDD + C4** — aggregates, domain events, context map, ubiquitous language, diagramas em 3 níveis.
- **Governança viva** — ADRs numerados, TRDs cross-cutting, 4 tipos de contratos de API (REST/async/gRPC/webhook), Design System.
- **Entrega rastreável** — PRDs, épicos, milestones com RAG status, tasks com lifecycle workflow, review de PR co-assinado por Code Reviewer + AppSec.
- **Observabilidade pós-entrega** — retros, incidentes 4-estado (open → mitigated → resolved → post-mortem) com timestamps auto-preenchidos.
- **Análise de grafo** — `sdlc-trace` (matriz de rastreabilidade PRD↔spec↔task↔review) e `sdlc-impact` (BFS forward/backward sobre wikilinks antes de mudar ou deprecar algo).
- **Dashboard HTML autocontido** — Kanban, Épicos & Milestones, Documentos, Domínio; sem servidor, via File System Access API.
- **Rastreamento de git worktrees** e status de PRs em SQLite.
- **Hook automático** PostToolUse que indexa cada `.md` salvo, rate-limited a 1 sinal / 5 s por vault.
- **Plugin language-agnostic + i18n do `_INDEX.md`** — código e templates em inglês; o LLM espelha a língua da conversa ao preencher conteúdo. O `_INDEX.md` e os `_MOC.md` por fase são renderizados na língua definida em `.sdlc-kit/marker.json:locale` (default `pt-br`, alternativo `en`), via `core/i18n.py`.

---

## Instalação

### Via Claude Code (recomendado)

No Claude Code, dentro de qualquer projeto Git:

```
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit
/reload-plugins
```

Pronto. Em seguida execute `/sdlc-kit:init` para criar o vault `.sdlc/` no projeto.

> Para pinar a uma versão específica: `/plugin marketplace add vellus-ai/sdlc-kit@v0.3.1`.

### Via instalador one-liner (alternativo — clona local e registra em settings.json)

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm "https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1?v=$(Get-Random)" | iex
```

> **Nota:** O `?v=$(Get-Random)` evita que o CDN do GitHub sirva uma versão em cache desatualizada. Se preferir omitir, a URL sem query string também funciona quando o cache já foi invalidado.

O script faz tudo automaticamente:

1. Verifica Python 3.11+, `git` e o `claude` CLI.
2. Clona o repositório em `~/.claude/plugins/sdlc-kit` (customizável via `SDLC_KIT_DIR=/outro/caminho`).
3. Instala o pacote Python com `pip install -e` (editable mode) e, opcionalmente, `pyyaml ≥ 6`.
4. Registra o plugin em `~/.claude/settings.json` (`extraKnownMarketplaces.sdlc-kit` + `enabledPlugins["sdlc-kit@sdlc-kit"] = true`).

Depois, **reinicie o Claude Code** e em qualquer projeto Git execute `/sdlc-kit:init`.

### Desinstalação

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.sh | bash
```

**Windows (PowerShell):**
```powershell
irm "https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.ps1?v=$(Get-Random)" | iex
```

O desinstalador remove o registro em `settings.json`, desinstala o pacote Python e apaga os arquivos do plugin. **Os vaults `.sdlc/` nos seus projetos permanecem intactos.**

### Instalação manual

**Pré-requisitos:**

| Ferramenta | Versão | Necessário para |
|-----------|--------|----------------|
| Python | 3.11+ | Core e scripts das skills |
| Claude Code CLI | qualquer | Registrar e invocar o plugin |
| `git` | qualquer | Skills de worktree, análise histórica |
| `gh` CLI | qualquer | Sync de status de PR (opcional) |
| PyYAML | ≥ 6 | Parser de frontmatter tolerante (opcional; o core tem fallback stdlib) |

```bash
git clone https://github.com/vellus-ai/sdlc-kit.git ~/.claude/plugins/sdlc-kit
cd ~/.claude/plugins/sdlc-kit
pip install -e ".[yaml]"          # ou ".[dev,yaml]" para trabalhar no plugin
sdlc-kit init-db
```

Em seguida, edite `~/.claude/settings.json` para adicionar:

```json
{
  "extraKnownMarketplaces": {
    "sdlc-kit": { "source": { "source": "github", "repo": "vellus-ai/sdlc-kit" } }
  },
  "enabledPlugins": { "sdlc-kit@sdlc-kit": true }
}
```

Reinicie o Claude Code.

---

## Uso rápido

Em qualquer projeto Git, abra o Claude Code e execute:

```
/sdlc-kit:init
```

Uma entrevista curta auto-detecta dono, remoto e tipo de projeto (greenfield vs brownfield), cria `.sdlc/` com as 8 fases canônicas, `CLAUDE.md`, `_INDEX.md`, `dashboard.html` e o banco SQLite.

### Fluxo típico de uma feature

```text
# 1 — Alinhamento de produto (01-planning)
/sdlc-kit:prd        → PRD da iniciativa

# 2 — Decisões e requisitos arquiteturais (02-architecture)
/sdlc-kit:adr        → Decisão tecnológica numerada (ADR-NNNN)
/sdlc-kit:trd        → Requisitos cross-cutting (performance, segurança, LGPD)
/sdlc-kit:c4         → Diagramas C4 Context/Container/Component
/sdlc-kit:api        → Contrato REST/async/gRPC/webhook

# 3 — Modelagem de domínio (03-domain)
/sdlc-kit:domain     → Aggregates, domain events, contratos ACL, context map

# 4 — Spec da feature (04-specs)
/sdlc-kit:spec       → Trio requirements.md (EARS) + design.md + tasks.md

# 5 — Execução (05-development)
/sdlc-kit:worktree   → Cria git worktree isolado + registra no vault
/sdlc-kit:task       → start / complete / block / reopen por TASK-NNN

# 6 — Revisão de PR (07-retrospectives/reviews)
/sdlc-kit:review     → Checklist Code Reviewer + AppSec, 6 seções, decisão

# 7 — Fechamento do ciclo (07-retrospectives)
/sdlc-kit:retro      → Retrospectiva de sprint
/sdlc-kit:incident   → Post-mortem de incidente, se houver

# A qualquer momento
/sdlc-kit:sync       → Revalida e regenera MOCs + _INDEX.md
/sdlc-kit:status     → Snapshot do vault
/sdlc-kit:trace      → Matriz PRD ↔ spec ↔ review
/sdlc-kit:impact --seed ADR-0007    → O que quebra se eu deprecar isto?
/sdlc-kit:dash       → Abre o dashboard no browser
```

---

## Catálogo completo de skills

Todas as skills seguem o contrato `list / scaffold / transition` (ou um verbo equivalente documentado no `SKILL.md`). Cada script emite um único objeto JSON em stdout com exit codes `0` (ok/dry-run) / `1` (erro do usuário) / `2` (erro fatal).

### Fase 00 — Steering

| Skill | Função |
|-------|-------|
| `/sdlc-kit:steer` | Atualiza os três docs de steering (`product.md`, `tech.md`, `standards.md`) em `00-steering/`. Transição `draft → active`. |

### Fase 01 — Planning

| Skill | Função |
|-------|-------|
| `/sdlc-kit:prd` | Product Requirements Document. Lifecycle `draft → active → shipped → archived`. |
| `/sdlc-kit:epic` | Épicos agrupando stories/specs. Lifecycle `planned → in-progress → done` + `cancelled`. |
| `/sdlc-kit:milestone` | Janela de entrega com RAG status (`planned → on-track → at-risk → slipped → done` + `cancelled`). Suporta `--target-date`. |

### Fase 02 — Architecture

| Skill | Função |
|-------|-------|
| `/sdlc-kit:adr` | Architecture Decision Record com numeração automática (MADR: `proposed → accepted/rejected → superseded/deprecated`). |
| `/sdlc-kit:trd` | Technical Requirements Document — NFRs cross-cutting (perf, scal, reliability, security, LGPD, observability, a11y, i18n, cost). Lifecycle `draft → approved → deprecated`. |
| `/sdlc-kit:c4` | Diagramas C4 em Mermaid, 3 níveis (context / container singletons + component coleção). |
| `/sdlc-kit:api` | Contratos de API em 4 estilos (`rest`, `async`, `grpc`, `webhook`). Lifecycle `draft → approved → deprecated`. |

### Fase 03 — Domain (DDD)

| Skill | Função |
|-------|-------|
| `/sdlc-kit:domain` | 5 kinds: `aggregate`, `event`, `contract` (coleções) + `context-map`, `ubiquitous-language` (singletons). Lifecycle comum `draft → approved → deprecated`. |

### Fase 04 — Specs (SDD)

| Skill | Função |
|-------|-------|
| `/sdlc-kit:spec` | Trio SDD `requirements.md` (EARS) + `design.md` + `tasks.md` por feature-slug, com portas de aprovação em cascata (`draft → approved → implemented → archived`). |

### Fase 05 — Development

| Skill | Função |
|-------|-------|
| `/sdlc-kit:worktree` | 2 kinds: `worktree` (lifecycle `active → merged / abandoned`) e `branch` (registro sem enum). |
| `/sdlc-kit:task` | Flips dos marcadores Kiro em `<feature>/tasks.md`: verbos `start / complete / block / reopen`. Apenas 1 task `[-]` ativa por feature por padrão. |

### Fase 06 — Design System

| Skill | Função |
|-------|-------|
| `/sdlc-kit:design-system` | 3 kinds: `token`, `component`, `pattern`. Lifecycle `draft → stable → deprecated`. |

### Fase 07 — Retrospectives & Observability

| Skill | Função |
|-------|-------|
| `/sdlc-kit:review` | Code review de PR co-assinado por **Senior Engineer + AppSec Engineer**. Dois eixos: `status (draft → final)` e `decision (pending → approved / approved-with-comments / changes-requested)`. |
| `/sdlc-kit:retro` | Retrospectiva de sprint/iteração. Lifecycle `draft → final`. Suporta `--sprint N`. |
| `/sdlc-kit:incident` | Post-mortem. 4 estados `open → mitigated → resolved → post-mortem` com auto-preenchimento de `mitigated_at` / `resolved_at`; enforce `SEV1..SEV4`. |

### Análise transversal (read-only)

| Skill | Função |
|-------|-------|
| `/sdlc-kit:trace` | Matriz de rastreabilidade PRD → spec-requirements → spec-design → spec-tasks → review. Detecta PRDs não implementados, designs órfãos, ADRs/TRDs nunca citados. Formatos `json` e `markdown`. |
| `/sdlc-kit:impact` | BFS sobre o grafo de wikilinks a partir de um seed, nas direções `forward` (o que este nó depende), `backward` (quem depende deste nó) ou `both`. Depth configurável (clampado a 10). |

### Operação

| Skill | Função |
|-------|-------|
| `/sdlc-kit:init` | Scaffold idempotente do vault. Auto-detecta dono, remoto, tipo (greenfield/brownfield). |
| `/sdlc-kit:sync` | Librarian: valida frontmatter por type, regenera todos os `_MOC.md` e o `_INDEX.md`, reporta anomalias (broken wikilinks, status inválido, duplicate titles, staleness). |
| `/sdlc-kit:status` | Snapshot JSON (contagens, worktrees ativos, ADRs proposed/accepted). Read-only. |
| `/sdlc-kit:doc` | Fallback: gera documento genérico a partir de qualquer template em `<phase>/_templates/` quando não há skill dedicada. |
| `/sdlc-kit:dash` | Abre o `dashboard.html` do vault no browser (cross-platform). |

---

## Dashboard

Após `/sdlc-kit:init`, abra `.sdlc/dashboard.html` diretamente no browser (Chrome/Edge recomendado — a File System Access API é requisito):

1. Clique em **Abrir Vault** → selecione a pasta `.sdlc/` do projeto.
2. Permissão concedida uma vez; handle salvo no IndexedDB para sessões futuras.

**4 abas disponíveis:**

| Aba | Funcionalidade |
|-----|---------------|
| **Tasks** | Kanban Backlog / Em Progresso / Concluído + Branch Graph com badges de PR |
| **Épicos & Milestones** | Cards com barra de progresso e indicador RAG por milestone |
| **Documentos** | Sidebar de arquivos, render markdown com wikilinks navegáveis |
| **Domínio** | Placeholder para bounded contexts (em expansão) |

Invoque a qualquer momento com `/sdlc-kit:dash`.

---

## Estrutura do vault

```text
.sdlc/
├── CLAUDE.md                    # Doutrina do vault — lida pelo agente antes de escrever
├── _INDEX.md                    # Índice vivo, regenerado pelo /sdlc-kit:sync
├── dashboard.html               # Dashboard autocontido
├── .sdlc-kit/
│   ├── marker.json              # Identifica a raiz do vault e a versão do kit
│   └── db.sqlite                # SQLite (WAL): notes, tasks, worktrees, events, ...
├── 00-steering/                 # product / tech / standards (steering docs)
│   └── _templates/
├── 01-planning/                 # PRDs, épicos, milestones
│   ├── prd/
│   ├── epic/
│   ├── milestone/
│   └── _templates/
├── 02-architecture/             # ADRs, TRDs, C4, API designs
│   ├── ADR/
│   ├── trd/
│   ├── c4/        (context.md, container.md, components/<slug>.md)
│   ├── api/       (rest/, async/, grpc/, webhook/)
│   └── _templates/
├── 03-domain/                   # DDD
│   ├── aggregates/
│   ├── events/
│   ├── contracts/
│   ├── context-map.md
│   ├── ubiquitous-language.md
│   └── _templates/
├── 04-specs/                    # Trios SDD por feature
│   └── <feature-slug>/ (requirements.md, design.md, tasks.md)
├── 05-development/              # Git worktrees e branches
│   ├── worktrees/
│   ├── branches/
│   └── _templates/
├── 06-design-system/            # Tokens, componentes, padrões
│   ├── tokens/
│   ├── components/
│   ├── patterns/
│   └── _templates/
└── 07-retrospectives/           # Reviews, retros, incidentes
    ├── reviews/
    ├── retros/
    ├── incidents/
    └── _templates/
```

---

## Arquitetura do plugin

```text
sdlc-kit/
├── .claude-plugin/
│   └── plugin.json              # Manifest: hook PostToolUse + descoberta automática de skills
├── core/                        # Biblioteca Python (stdlib-only por design)
│   ├── paths.py                 # Descoberta de vault via ancestrais
│   ├── db.py                    # SQLite + migrations idempotentes (modo WAL, FK)
│   ├── scanner.py               # Delta scan por mtime → hash → reparse
│   ├── parser.py                # Frontmatter (YAML opcional, fallback stdlib) + wikilinks
│   ├── git.py                   # git worktree list + gh pr list → SQLite
│   ├── cli.py                   # Ponto de entrada `sdlc-kit` (init-db, scan, status, rebuild-db)
│   └── migrations/              # Esquema SQLite versionado
├── hooks/
│   └── post-vault-write.py      # PostToolUse, rate-limited 1/5s por vault
├── skills/
│   └── sdlc-<nome>/
│       ├── SKILL.md             # Contrato: quando invocar, fluxo, personas, guardrails
│       └── scripts/<nome>.py    # Sempre emite JSON; exit 0/1/2; stdlib-only
├── assets/
│   └── vault-tree/              # Templates por fase + dashboard.html
├── tests/                       # pytest (core + todas as skills)
├── install.sh / install.ps1     # Instaladores one-liner
├── uninstall.sh / uninstall.ps1 # Desinstaladores (preservam vaults)
└── pyproject.toml
```

**Regras de extensão:**

1. Ler `CLAUDE.md` do vault antes de qualquer escrita — ele é soberano.
2. Seguir o registry de types + status enums em `skills/sdlc-sync/scripts/sync.py` (fonte da verdade para validação de frontmatter).
3. Invocar `/sdlc-kit:sync` ao fim de qualquer skill que modifique notas.
4. Nunca editar o `CLAUDE.md` de dentro de uma skill.
5. Notas geradas devem carregar `status: draft` e `generated_by: <nome-da-skill>`.
6. Artefatos persistentes em inglês; o LLM espelha a língua da conversa do usuário ao preencher conteúdo.

---

## CLI

```bash
sdlc-kit init-db      # Inicializa o banco SQLite (8 tabelas)
sdlc-kit scan         # Delta scan incremental do vault
sdlc-kit rebuild-db   # Reprocessa o vault inteiro do zero
sdlc-kit status       # Resumo JSON de saúde do vault
sdlc-kit version      # Versão instalada
```

---

## Desenvolvimento

```bash
# Clonar e instalar com dev deps
git clone https://github.com/vellus-ai/sdlc-kit.git
cd sdlc-kit
pip install -e ".[dev,yaml]"

# Rodar os testes
pytest                                   # suite completa
pytest tests/test_scanner.py             # arquivo específico
pytest --cov=core --cov-report=html      # cobertura

# Instalar em modo editável para iterar localmente
pip install -e .
```

### Convenções

- Branch: `feat/<slug>` ou `fix/<slug>`.
- TDD sempre que possível — teste antes da implementação.
- Scripts em `skills/` sempre com `--dry-run` e saída JSON única em stdout.
- Erros em `.sdlc-kit/<skill>-errors.log`; nunca travam a operação principal.
- Cobertura mínima: 90% nos módulos `core/`.

### Anatomia de uma skill

```text
skills/sdlc-<nome>/
├── SKILL.md          # YAML header: name + description (triggers EN + pt-BR)
│                     # Personas (lens duo/triad), fluxo, guardrails, exemplos
├── scripts/
│   └── <nome>.py     # list / scaffold / transition (ou verbos equivalentes)
│                     # --dry-run obrigatório; JSON stdout; exit 0/1/2
└── references/       # Opcional: docs de contexto para o LLM
```

Cada skill declara no `sync.py` registry seu type (ex: `domain-aggregate`, `c4-component`, `api-rest`), campos obrigatórios de frontmatter e enum de status — o librarian usa isso para validar tudo.

---

## Contribuição

1. Fork o repositório.
2. Crie uma branch: `feat/<slug>`.
3. Implemente com TDD.
4. Abra PR descrevendo **o quê** e **por quê**.

Para reportar bugs ou sugerir features: [abra uma issue](https://github.com/vellus-ai/sdlc-kit/issues).

---

## Licença

[MIT](LICENSE) © 2026 [Vellus AI](https://github.com/vellus-ai)
