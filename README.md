# SDLC Kit

> Spec-Driven Development (SDD) + Domain-Driven Design (DDD) vault for **Claude Code**, versioned inside your Git repo — Obsidian-compatible, LLM-optimized, language-agnostic.

[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?logo=anthropic)](https://claude.ai/code) [![Skills](https://img.shields.io/badge/skills-22-blueviolet)](https://github.com/vellus-ai/sdlc-kit/tree/main/plugins) [![Phases](https://img.shields.io/badge/phases-8-informational)](#vault-structure) [![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![Version](https://img.shields.io/badge/version-0.4.0-orange)](https://github.com/vellus-ai/sdlc-kit/releases/tag/v0.4.0)

> 📖 **Este documento também está disponível em [Português (Brasil)](#português-brasil) abaixo.**

---

## Why it exists

When you work with Claude Code on real projects, three problems surface again and again:

- **Architectural decisions get lost** between sessions — the LLM has no context on what was decided.
- **Requirements drift out of sync** with implementation — the code moves forward, the spec falls behind.
- **Every new session starts from zero** — no history of ADRs, epics, domain, incidents.

SDLC Kit solves this by maintaining a versioned `.sdlc/` vault inside your own repo, with automatic indexing, **22 skills** across the full lifecycle (planning → architecture → domain → specs → development → design-system → retrospectives), and a self-contained HTML dashboard.

---

## Two composable plugins

Starting at **v0.4.0**, SDLC Kit ships as **two plugins** in the same marketplace. Install just the core for the daily PR loop; add the extended pack when you need governance, architecture modeling and post-delivery analysis.

| Plugin | Skills | Install | Purpose |
|---|---|---|---|
| **`sdlc-kit`** (core) | 11 | `/plugin install sdlc-kit@sdlc-kit` | Daily delivery loop: init, sync, status, dash, prd, adr, spec, task, worktree, review, retro. |
| **`sdlc-kit-extended`** | 11 (optional) | `/plugin install sdlc-kit-extended@sdlc-kit` | Governance (trd, epic, milestone, steer), architecture & domain (c4, api, domain, design-system), ops/analysis (incident, trace, impact). Requires the core plugin. |

---

## Features

- **Canonical 8-phase vault** (`00-steering` → `07-retrospectives`).
- **22 skills** invokable via `/sdlc-kit:<name>`, each with a stable `list / scaffold / transition` contract.
- **SDD** — `requirements.md` (EARS) + `design.md` + `tasks.md` trio per feature, with approval gates.
- **DDD + C4** — aggregates, domain events, context map, ubiquitous language, 3-level diagrams.
- **Living governance** — auto-numbered ADRs, cross-cutting TRDs, 4 API contract styles (REST/async/gRPC/webhook), Design System.
- **Traceable delivery** — PRDs, epics, milestones with RAG status, task lifecycle workflow, PR review co-signed by Code Reviewer + AppSec.
- **Post-delivery observability** — retros, 4-state incidents (open → mitigated → resolved → post-mortem) with auto-populated timestamps.
- **Graph analysis** — `sdlc-trace` (PRD↔spec↔task↔review matrix) and `sdlc-impact` (forward/backward BFS on wikilinks).
- **Self-contained HTML dashboard** — Kanban, Epics & Milestones, Documents, Domain; no server, via File System Access API.
- **Git worktree + PR tracking** in SQLite.
- **PostToolUse hook** re-indexes every saved `.md`, rate-limited to 1 signal / 5 s per vault.
- **i18n of `_INDEX.md`** — rendered in the language set at `.sdlc-kit/marker.json:locale` (default `pt-br`, alternate `en`). Code and templates stay English; the LLM mirrors your chat language in content.

---

## Install

### Via Claude Code marketplace (recommended)

Inside any Git project:

```
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit            # core — required
/plugin install sdlc-kit-extended@sdlc-kit   # optional extended skills
/reload-plugins
```

Then run `/sdlc-kit:init` to scaffold `.sdlc/`.

> Pin a version: `/plugin marketplace add vellus-ai/sdlc-kit@v0.4.0`.

### One-liner installer (alternative — clones locally and registers in settings.json)

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm "https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/install.ps1?v=$(Get-Random)" | iex
```

The installer checks Python 3.11+, `git` and the `claude` CLI; clones the repo to `~/.claude/plugins/sdlc-kit`; installs the Python package via `pip install -e`; and registers the plugins in `~/.claude/settings.json`.

### Uninstall

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.sh | bash
```

**Windows (PowerShell):**
```powershell
irm "https://raw.githubusercontent.com/vellus-ai/sdlc-kit/main/uninstall.ps1?v=$(Get-Random)" | iex
```

`.sdlc/` vaults inside your projects are **preserved**.

---

## Quick start

```
/sdlc-kit:init
```

A short interview auto-detects owner, remote and project type (greenfield vs brownfield), creates `.sdlc/` with the 8 canonical phases, `CLAUDE.md`, `_INDEX.md`, `dashboard.html` and the SQLite tracker.

### Typical feature flow

```text
# 1 — Product alignment (01-planning)
/sdlc-kit:prd        → initiative PRD

# 2 — Architectural decisions & requirements (02-architecture)
/sdlc-kit:adr        → numbered technical decision (ADR-NNNN)
/sdlc-kit:trd        → cross-cutting requirements (extended)
/sdlc-kit:c4         → C4 Context/Container/Component diagrams (extended)
/sdlc-kit:api        → REST/async/gRPC/webhook contract (extended)

# 3 — Domain modeling (03-domain, extended)
/sdlc-kit:domain     → aggregates, events, ACL contracts, context map

# 4 — Feature spec (04-specs)
/sdlc-kit:spec       → trio requirements.md (EARS) + design.md + tasks.md

# 5 — Execution (05-development)
/sdlc-kit:worktree   → isolated git worktree + vault record
/sdlc-kit:task       → start / complete / block / reopen a TASK-NNN

# 6 — PR review
/sdlc-kit:review     → Code Reviewer + AppSec checklist, 6 sections, decision

# 7 — Cycle close
/sdlc-kit:retro      → sprint retrospective
/sdlc-kit:incident   → post-mortem (extended)

# Anytime
/sdlc-kit:sync       → revalidate and regenerate MOCs + _INDEX.md
/sdlc-kit:status     → vault snapshot
/sdlc-kit:trace      → PRD ↔ spec ↔ review matrix (extended)
/sdlc-kit:impact --seed ADR-0007    → what breaks if I deprecate this? (extended)
/sdlc-kit:dash       → open the dashboard in the browser
```

---

## Vault structure

```text
.sdlc/
├── CLAUDE.md                    # vault doctrine — read by the agent before any write
├── _INDEX.md                    # living index, regenerated by /sdlc-kit:sync
├── dashboard.html               # self-contained dashboard
├── .sdlc-kit/
│   ├── marker.json              # vault root + kit version + locale
│   └── db.sqlite                # SQLite (WAL): notes, tasks, worktrees, events, …
├── 00-steering/                 # product / tech / standards
├── 01-planning/                 # PRDs, epics, milestones
├── 02-architecture/             # ADRs, TRDs, C4, API designs
├── 03-domain/                   # DDD artifacts
├── 04-specs/                    # SDD trios per feature
├── 05-development/              # git worktrees & branches
├── 06-design-system/            # tokens, components, patterns
└── 07-retrospectives/           # reviews, retros, incidents
```

---

## Development

```bash
git clone https://github.com/vellus-ai/sdlc-kit.git
cd sdlc-kit
pip install -e ".[dev,yaml]"

pytest                                   # full suite
pytest tests/test_scanner.py             # specific file
pytest --cov=core --cov-report=html      # coverage
```

### Conventions

- Branches: `feat/<slug>` or `fix/<slug>`.
- TDD is the default — test before implementation.
- Every skill script supports `--dry-run` and emits a single JSON object to stdout; exit codes `0` / `1` / `2`.
- Minimum coverage: 90% on `core/` modules.

---

## Documentation

- **Architecture** — [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Contributing** — [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- **Publishing** — [`docs/PUBLISHING.md`](docs/PUBLISHING.md)
- **Testing** — [`docs/TESTING.md`](docs/TESTING.md)
- **Privacy policy** — [`PRIVACY.md`](PRIVACY.md)
- **Changelog** — [`CHANGELOG.md`](CHANGELOG.md)

---

## Contributing

1. Fork the repository.
2. Create a branch: `feat/<slug>`.
3. Implement with TDD.
4. Open a PR describing **what** and **why**.

Bugs or feature requests: [open an issue](https://github.com/vellus-ai/sdlc-kit/issues).

---

## License

[MIT](LICENSE) © 2026 [Vellus](https://vellus.tech/)

---
---

## Português (Brasil)

> Vault de **Spec-Driven Development (SDD)** + **Domain-Driven Design (DDD)** para o **Claude Code**, versionado dentro do seu repositório Git — compatível com Obsidian, otimizado para LLMs, agnóstico de linguagem.

### Problema que resolve

Ao trabalhar com Claude Code em projetos reais, três problemas surgem constantemente:

- **Decisões arquiteturais se perdem** entre sessões — o LLM não tem contexto do que foi decidido.
- **Requisitos saem de sincronia** com a implementação — o código avança, a spec fica para trás.
- **Cada nova sessão começa do zero** — sem histórico de ADRs, épicos, domínio, incidentes.

O SDLC Kit resolve isso mantendo um vault `.sdlc/` versionado no seu próprio repo, com indexação automática, **22 skills** cobrindo o ciclo completo (planning → architecture → domain → specs → development → design-system → retrospectives) e um dashboard HTML autocontido.

### Dois plugins compostos

A partir da **v0.4.0**, o SDLC Kit é distribuído como **dois plugins** no mesmo marketplace. Instale só o core para o ciclo de PR diário; adicione o extended quando precisar de governança, modelagem arquitetural e análise pós-entrega.

| Plugin | Skills | Instalação | Propósito |
|---|---|---|---|
| **`sdlc-kit`** (core) | 11 | `/plugin install sdlc-kit@sdlc-kit` | Ciclo de entrega diário: init, sync, status, dash, prd, adr, spec, task, worktree, review, retro. |
| **`sdlc-kit-extended`** | 11 (opcional) | `/plugin install sdlc-kit-extended@sdlc-kit` | Governança (trd, epic, milestone, steer), arquitetura & domínio (c4, api, domain, design-system), ops/análise (incident, trace, impact). Requer o plugin core. |

### Instalação

Dentro de qualquer projeto Git no Claude Code:

```
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit            # core — obrigatório
/plugin install sdlc-kit-extended@sdlc-kit   # skills extended (opcional)
/reload-plugins
```

Depois execute `/sdlc-kit:init` para criar o vault `.sdlc/`.

> Pinar uma versão: `/plugin marketplace add vellus-ai/sdlc-kit@v0.4.0`.

### Uso rápido

Execute `/sdlc-kit:init` dentro do seu projeto. Uma entrevista curta auto-detecta dono, remoto e tipo (greenfield / brownfield) e cria as 8 fases canônicas, o `CLAUDE.md`, o `_INDEX.md`, o `dashboard.html` e o SQLite tracker.

### Funcionalidades

- Vault estruturado em **8 fases canônicas** (`00-steering` → `07-retrospectives`).
- **22 skills** invocáveis via `/sdlc-kit:<nome>`, cada uma com contrato `list / scaffold / transition` estável.
- **SDD** — trio `requirements.md` (EARS) + `design.md` + `tasks.md` por feature, com portas de aprovação.
- **DDD + C4** — aggregates, domain events, context map, ubiquitous language, diagramas em 3 níveis.
- **Governança viva** — ADRs numerados, TRDs cross-cutting, 4 tipos de contratos de API (REST/async/gRPC/webhook), Design System.
- **Entrega rastreável** — PRDs, épicos, milestones com RAG status, task lifecycle workflow, review de PR co-assinado por Code Reviewer + AppSec.
- **Observabilidade pós-entrega** — retros, incidentes 4-estado com timestamps auto-preenchidos.
- **Análise de grafo** — `sdlc-trace` (matriz PRD↔spec↔task↔review) e `sdlc-impact` (BFS forward/backward).
- **Dashboard HTML autocontido** — Kanban, Épicos & Milestones, Documentos, Domínio; sem servidor.
- **Rastreamento de git worktrees e PRs** em SQLite.
- **Hook PostToolUse** que indexa cada `.md` salvo, rate-limited a 1 sinal / 5 s por vault.
- **i18n do `_INDEX.md`** — renderizado no idioma definido em `.sdlc-kit/marker.json:locale` (default `pt-br`, alternativo `en`). Código e templates em inglês; o LLM espelha o idioma da conversa no conteúdo.

### Desenvolvimento

```bash
git clone https://github.com/vellus-ai/sdlc-kit.git
cd sdlc-kit
pip install -e ".[dev,yaml]"
pytest
```

**Convenções:** branches `feat/<slug>` ou `fix/<slug>`; TDD por padrão; cada script emite JSON em stdout com exit codes `0` / `1` / `2`; cobertura mínima 90% em `core/`.

### Documentação

- **Arquitetura** — [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Contribuição** — [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- **Publicação** — [`docs/PUBLISHING.md`](docs/PUBLISHING.md)
- **Testes** — [`docs/TESTING.md`](docs/TESTING.md)
- **Política de privacidade** — [`PRIVACY.md`](PRIVACY.md)
- **Changelog** — [`CHANGELOG.md`](CHANGELOG.md)

### Licença

[MIT](LICENSE) © 2026 [Vellus](https://vellus.tech/)
