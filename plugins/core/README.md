<div align="center">

# 📝 sdlc-kit — *core*

### *The daily delivery loop for Claude Code projects*

11 Claude Code skills that scaffold and maintain the **core artifacts of every feature cycle** — vault bootstrap, PRDs, ADRs, SDD specs, tasks, git worktrees, code reviews, sprint retros — all backed by an auto-indexed Obsidian-compatible vault.

<p>
  <a href="https://claude.ai/code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?logo=anthropic"></a>
  <img alt="Skills" src="https://img.shields.io/badge/skills-11-blueviolet">
  <img alt="Version" src="https://img.shields.io/badge/version-0.4.0-orange">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

</div>

> 📖 **Também disponível em [Português (Brasil)](#português-brasil).**

---

## 🚀 Install

```text
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit
/reload-plugins
```

Then, in any Git repo:

```text
/sdlc-kit:init
```

---

## 🎯 The 11 skills

### 🧰 Infrastructure

| Skill | One-liner |
|---|---|
| `/sdlc-kit:init` | Scaffold `.sdlc/` vault (idempotent, auto-detects owner/remote/greenfield) |
| `/sdlc-kit:sync` | Librarian: revalidates frontmatter, regenerates every `_MOC.md` and `_INDEX.md`, reports anomalies |
| `/sdlc-kit:status` | Snapshot JSON: counts per phase, active worktrees, proposed/accepted ADRs |
| `/sdlc-kit:dash` | Opens the self-contained `dashboard.html` in the default browser |

### 📑 Daily delivery artifacts

| Skill | Path | Lifecycle |
|---|---|---|
| `/sdlc-kit:prd` | `01-planning/prd/<slug>.md` | `draft → active → shipped → archived` |
| `/sdlc-kit:adr` | `02-architecture/adr/ADR-NNNN-<slug>.md` | MADR: `proposed → accepted/rejected → superseded/deprecated` |
| `/sdlc-kit:spec` | `04-specs/<feature>/{requirements,design,tasks}.md` | per-doc: `draft → approved → implemented → archived` |
| `/sdlc-kit:task` | Flips `[ ]` / `[-]` / `[x]` / `[~]` markers inside `<feature>/tasks.md` | verbs `start / complete / block / reopen` |
| `/sdlc-kit:worktree` | `05-development/worktrees/<slug>.md` (+ `branches/<slug>.md`) | worktree: `active → merged / abandoned` |
| `/sdlc-kit:review` | `07-retrospectives/reviews/<slug>.md` | two axes — `status`: `draft → final` · `decision`: `pending → approved / approved-with-comments / changes-requested` |
| `/sdlc-kit:retro` | `07-retrospectives/retros/<slug>.md` | `draft → final` (optional `--sprint N`) |

---

## 🧩 Need more? Install `sdlc-kit-extended`

If you adopt DDD seriously, track governance (TRDs, epics, milestones), care about traceability matrices or post-mortems, the extension plugin adds 11 more skills:

```text
/plugin install sdlc-kit-extended@sdlc-kit
```

See [`../extended/`](../extended/README.md).

---

## 🔬 Under the hood

- **Contract** — every skill implements `list / scaffold / transition` and emits a single JSON object on stdout; exit codes `0/1/2`.
- **SQLite tracker** at `.sdlc-kit/db.sqlite` (WAL mode) indexes notes, tasks, decisions, worktrees, events.
- **PostToolUse hook** (rate-limited 1 signal / 5 s per vault) emits an `additionalContext` cue telling Claude to re-sync after every `.md` save inside the vault.
- **Frontmatter regex + i18n messages + helpers** centralized in `core/{regexes,frontmatter,i18n,paths,scanner,db,parser,git,cli}.py` — 100% coverage on the canonical modules.

---

## 🌐 Languages

The vault's `_INDEX.md` and phase MOCs are rendered in the language defined in `.sdlc-kit/marker.json:locale` (default `pt-br`, alternative `en`). The LLM mirrors the user's chat language in narrative sections.

---

## 🔗 Links

- Parent repo & full docs: [`vellus-ai/sdlc-kit`](https://github.com/vellus-ai/sdlc-kit)
- Extension plugin: [`sdlc-kit-extended`](../extended/README.md)
- Publishing guide: [`../../docs/PUBLISHING.md`](../../docs/PUBLISHING.md)
- Architecture: [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)

[MIT](../../LICENSE) © 2026 [Vellus](https://vellus.tech/)

---
---

## Português (Brasil)

### *O ciclo diário de entrega para projetos Claude Code*

11 skills Claude Code que fazem scaffolding e manutenção dos **artefatos centrais de todo ciclo de feature** — bootstrap de vault, PRDs, ADRs, specs SDD, tasks, worktrees git, code reviews, retros de sprint — respaldados por um vault compatível com Obsidian auto-indexado.

### Instalação

```text
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit
/reload-plugins
```

Depois, em qualquer repo Git:

```text
/sdlc-kit:init
```

### As 11 skills

#### 🧰 Infraestrutura

| Skill | Descrição |
|---|---|
| `/sdlc-kit:init` | Scaffold do vault `.sdlc/` (idempotente, auto-detecta dono/remoto/greenfield) |
| `/sdlc-kit:sync` | Librarian: revalida frontmatter, regenera todos os `_MOC.md` e `_INDEX.md`, reporta anomalias |
| `/sdlc-kit:status` | Snapshot JSON: contagens por fase, worktrees ativos, ADRs proposed/accepted |
| `/sdlc-kit:dash` | Abre o `dashboard.html` autocontido no navegador default |

#### 📑 Artefatos de entrega diária

| Skill | Caminho | Lifecycle |
|---|---|---|
| `/sdlc-kit:prd` | `01-planning/prd/<slug>.md` | `draft → active → shipped → archived` |
| `/sdlc-kit:adr` | `02-architecture/adr/ADR-NNNN-<slug>.md` | MADR: `proposed → accepted/rejected → superseded/deprecated` |
| `/sdlc-kit:spec` | `04-specs/<feature>/{requirements,design,tasks}.md` | por-doc: `draft → approved → implemented → archived` |
| `/sdlc-kit:task` | Flipa marcadores `[ ]` / `[-]` / `[x]` / `[~]` em `<feature>/tasks.md` | verbos `start / complete / block / reopen` |
| `/sdlc-kit:worktree` | `05-development/worktrees/<slug>.md` (+ `branches/<slug>.md`) | worktree: `active → merged / abandoned` |
| `/sdlc-kit:review` | `07-retrospectives/reviews/<slug>.md` | dois eixos — `status`: `draft → final` · `decision`: `pending → approved / approved-with-comments / changes-requested` |
| `/sdlc-kit:retro` | `07-retrospectives/retros/<slug>.md` | `draft → final` (opcional `--sprint N`) |

### Precisa de mais? Instale `sdlc-kit-extended`

Se você adota DDD a sério, rastreia governança (TRDs, épicos, milestones), se importa com matrizes de rastreabilidade ou post-mortems, o plugin de extensão adiciona 11 skills:

```text
/plugin install sdlc-kit-extended@sdlc-kit
```

### Links

- Repo principal: [`vellus-ai/sdlc-kit`](https://github.com/vellus-ai/sdlc-kit)
- Plugin extended: [`sdlc-kit-extended`](../extended/README.md)
- Guia de publicação: [`../../docs/PUBLISHING.md`](../../docs/PUBLISHING.md)
- Arquitetura: [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)

[MIT](../../LICENSE) © 2026 [Vellus](https://vellus.tech/)
