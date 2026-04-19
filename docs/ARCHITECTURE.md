# Architecture

> 📖 **Also available in [Português (Brasil)](#arquitetura--português-brasil) below.**

This document describes how the SDLC Kit plugin is structured, how its pieces fit together, and the design decisions that shape the codebase.

## Goals

- **Low-friction onboarding.** `/sdlc-kit:init` asks one question and scaffolds the vault.
- **Single source of truth.** The vault on disk — not a database — is authoritative. SQLite is a derived index, always regenerable by re-running the librarian.
- **Language-agnostic plugin, multilingual UX.** Code and templates stay in English; the LLM mirrors the user's chat language. See [ADR-0004](decisions/ADR-0004-i18n-strategy.md).
- **Local-first and stdlib-first.** No network calls at scaffold/scan time; `core/` uses only the Python standard library where possible.

## C4 Level 1 — System context

```
┌───────────────────────────────────────────────────────────────────┐
│                         Claude Code (host)                        │
│                                                                   │
│   ┌─────────────────────────┐   ┌──────────────────────────┐      │
│   │ User (developer / PM /  │──▶│    Claude LLM agent      │      │
│   │        architect)       │   └────────────┬─────────────┘      │
│   └─────────────────────────┘                │                    │
│                                              ▼                    │
│                               ┌─────────────────────────────┐     │
│                               │      SDLC Kit plugin        │     │
│                               │ (skills + hooks + core lib) │     │
│                               └────────────┬────────────────┘     │
└────────────────────────────────────────────┼──────────────────────┘
                                             │
                                             ▼
                    ┌────────────────────────────────────────────┐
                    │      Project repository (Git)              │
                    │   ├─ <repo>/                               │
                    │   │   ├─ .sdlc/           ← the vault      │
                    │   │   │   ├─ CLAUDE.md                     │
                    │   │   │   ├─ _INDEX.md                     │
                    │   │   │   ├─ 00-steering/ … 07-retros/     │
                    │   │   │   └─ .sdlc-kit/                    │
                    │   │   │       ├─ marker.json               │
                    │   │   │       └─ db.sqlite                 │
                    │   │   └─ CLAUDE.md (root)                  │
                    └────────────────────────────────────────────┘
```

External dependencies are deliberately minimal: Git (always), optional `gh` CLI for greenfield repo creation, optional Python dependencies behind `pyproject.toml` extras (`[dev]`, `[yaml]`).

## C4 Level 2 — Containers

```
┌──────────────────────── SDLC Kit plugin ─────────────────────────┐
│                                                                  │
│  ┌─────────────┐        ┌─────────────┐       ┌──────────────┐   │
│  │  Skills     │        │    Hooks    │       │  CLI         │   │
│  │ (22 skills) │        │ PostToolUse │       │ sdlc-kit     │   │
│  └──────┬──────┘        └──────┬──────┘       └──────┬───────┘   │
│         │ subprocess           │ Python                │         │
│         ▼                      ▼                       ▼         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   core library                             │  │
│  │  paths │ db │ parser │ scanner │ frontmatter │ regexes │   │  │
│  │                      git │ i18n │ migrations              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                 ┌─────────────────────────┐                      │
│                 │  assets/vault-tree/     │                      │
│                 │  (canonical templates)  │                      │
│                 └─────────────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
```

### Skills (`plugins/{core,extended}/skills/sdlc-*/`)

Each skill is a self-contained directory:

- `SKILL.md` — YAML frontmatter + prose doctrine. The LLM reads this before acting.
- `scripts/<name>.py` — deterministic Python entry point. JSON on stdout, exit codes `0|1|2`. Never mutates without explicit action.
- `references/` (optional) — context docs the LLM should read for specific sections.
- `assets/` (optional) — templates, static files (e.g., the vault tree under `sdlc-init`).

The 22 skills span 8 SDLC phases, split across two composable plugins (`plugins/core` — 11 skills; `plugins/extended` — 11 skills). See [ADR-0002](decisions/ADR-0002-skills-inventory.md).

### Hooks (`hooks/`)

The single hook is `post-vault-write.py`, wired to `PostToolUse` in `.claude-plugin/plugin.json`. It fires after any Write/Edit/NotebookEdit and:

1. Walks ancestor directories to locate `.sdlc-kit/marker.json`.
2. If the modified path is inside a vault, records a `note_created` / `note_updated` / `note_deleted` event in `db.sqlite`.
3. Emits `additionalContext` back to the LLM (rate-limited to once per 5 s per vault) asking it to run the librarian.

If the DB is unreachable, the hook degrades silently — it never blocks a write.

### CLI (`core/cli.py`)

The `sdlc-kit` command exposes the same primitives the skills use internally:

- `sdlc-kit init-db` — create the SQLite tracker.
- `sdlc-kit scan` — incremental delta scan.
- `sdlc-kit rebuild-db` — full reprocess.
- `sdlc-kit status` — health snapshot.
- `sdlc-kit version` — plugin version.

### Core library (`core/`)

- **`paths.py`** — vault discovery by walking ancestors for `.sdlc-kit/marker.json`.
- **`db.py`** — SQLite connection with WAL mode, FK constraints, and idempotent migrations from `core/migrations/`.
- **`scanner.py`** — 3-level delta: `mtime` → `hash` → `reparse`. Most scans skip files without rereading them.
- **`parser.py`** — frontmatter + wikilink parser for `.md` files.
- **`frontmatter.py`** — typed frontmatter accessors.
- **`regexes.py`** — shared regex library (slug, wikilink, etc.).
- **`git.py`** — thin wrappers over `git` for detection and remote resolution.
- **`i18n.py`** — `t(locale, key, **kwargs)` resolver with pt-BR primary and en fallback.
- **`migrations/`** — one SQL file per schema version, applied in order.

## Data flow

### Scaffold flow (`/sdlc-kit:init`)

```
User      Skill (sdlc-init)          scaffold.py           Filesystem
 │                │                       │                     │
 │─ /sdlc-kit:init                        │                     │
 │                │─ read SKILL.md        │                     │
 │                │─ run detect.py        │                     │
 │                │◀ JSON repo facts ─────│                     │
 │── confirm ────▶│                       │                     │
 │                │─ run scaffold.py ────▶│                     │
 │                │                       │─ copy vault-tree ──▶│
 │                │                       │─ write marker.json ▶│
 │                │                       │─ init SQLite ──────▶│
 │                │◀ JSON summary ────────│                     │
 │◀── report ─────│                       │                     │
```

### Librarian flow (`/sdlc-kit:sync`)

```
(trigger: manual or hook)
        │
        ▼
   sync.py
        │
        ├─▶ core.scanner.scan()        ← 3-level delta, writes events to db.sqlite
        │
        ├─▶ validate frontmatter       ← REQUIRED_FIELDS_BY_TYPE / VALID_STATUS_BY_TYPE
        │
        ├─▶ check wikilinks            ← flags dangling targets
        │
        ├─▶ regenerate <phase>/_MOC.md ← `## Artifacts` section only
        │
        ├─▶ rewrite _INDEX.md          ← canonical 8-phase structure
        │
        └─▶ emit JSON report           ← scanned, db_changes, anomalies, regenerated
```

## Patterns

### list / scaffold / transition

Every authoring skill (adr, prd, epic, milestone, spec, trd, review, task, domain, design-system) follows the same three-action contract:

- **`list`** — read-only enumeration; returns `count` and an array of `{slug, path, status, …}`.
- **`scaffold` / `new`** — copies a template into the right location; refuses to overwrite without `--force`.
- **`transition`** — flips the `status:` (or `decision:`) frontmatter field along a defined lifecycle; idempotent when already at target.

Each script emits a single JSON object on stdout. Exit codes: `0` success or dry-run, `1` user error, `2` fatal. This uniformity makes the skills composable and testable the same way.

### Registry in `sync.py`

The librarian is the single source of truth for valid doc types and their lifecycles. Two constants drive validation:

- **`REQUIRED_FIELDS_BY_TYPE`** — required frontmatter fields per `type:` (e.g., `prd` requires `status`, `owner`, `updated`).
- **`VALID_STATUS_BY_TYPE`** — allowed `status:` enum per type.

Adding a new doc type means updating **both** constants and registering the new skill in `.claude-plugin/plugin.json`. No other place in the codebase enumerates types — everything else reads them from `sync.py`. This makes the librarian the schema registry.

### Hook rate limiting

The PostToolUse hook fires on every write, but we don't want the LLM spamming `/sdlc-kit:sync` after every keystroke. The hook keeps a per-vault timestamp in `db.sqlite` (`events` table, last `hook_fired` row) and only emits `additionalContext` when at least 5 seconds have elapsed since the previous emission for that vault.

## Schema

SQLite lives at `.sdlc-kit/db.sqlite` and uses WAL mode. Schema is versioned; migrations in `core/migrations/` are applied idempotently.

Core tables: `notes`, `tags`, `note_tags`, `aliases`, `links`, `areas`, `events`. Additional tables support analytics (`suggestions_cache`, `alerts_cache`) and clustering (`clusters`, `cluster_notes`, `duplicate_candidates`).

The schema is derivable — losing `db.sqlite` is recoverable via `sdlc-kit rebuild-db`, which re-walks the vault and repopulates everything.

## Vault structure

Every vault has:

- `.obsidian-master/marker.json` (legacy) or `.sdlc-kit/marker.json` — root identifier, kit version, project metadata.
- `CLAUDE.md` — the doctrine. User-owned. The LLM reads it before any write and must never edit it from inside a skill.
- `_INDEX.md` — regenerated by the librarian. Never edit manually.
- 8 numbered phases (`00-steering` through `07-retrospectives`) each with its own `_MOC.md` and `_templates/`.

See [ADR-0001](decisions/ADR-0001-estrutura-canonica.md) for why the 8-phase layout is fixed.

## Extension points

When you add a new skill:

1. Design the trigger phrases (English + pt-BR), the persona(s), and the lifecycle.
2. Scaffold `skills/sdlc-<name>/` with `SKILL.md` + `scripts/<name>.py`.
3. Honor the script contract: JSON stdout, exit codes `0|1|2`, `--dry-run` for mutations.
4. Register the doc type in `sync.py` (`REQUIRED_FIELDS_BY_TYPE`, `VALID_STATUS_BY_TYPE`).
5. Register the skill in `.claude-plugin/plugin.json`.
6. Add tests under `tests/test_<name>_skill.py` using the helpers in `tests/_skill_helpers.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the end-to-end workflow.

---
---

## Arquitetura — Português (Brasil)

> A versão canônica deste documento é a **inglesa acima**. Esta seção é um resumo em português.

Este documento descreve como o plugin SDLC Kit é estruturado, como suas peças se encaixam, e as decisões de design que moldam o código-base.

### Objetivos

- **Onboarding sem atrito.** `/sdlc-kit:init` faz uma pergunta e cria o vault.
- **Única fonte de verdade.** O vault em disco — não um banco — é autoritativo. SQLite é um índice derivado, sempre regenerável pela skill librarian.
- **Plugin agnóstico de linguagem, UX multilíngue.** Código e templates permanecem em inglês; o LLM espelha o idioma da conversa. Ver [ADR-0004](decisions/ADR-0004-i18n-strategy.md).
- **Local-first e stdlib-first.** Sem chamadas de rede no scaffold/scan; `core/` usa só a stdlib Python onde possível.

### Visão geral

- **22 skills** em 8 fases SDLC, distribuídas em 2 plugins compostos (`plugins/core` com 11 skills do ciclo diário; `plugins/extended` com 11 skills opcionais de governança/arquitetura/análise).
- **Hook PostToolUse** em `plugins/core/hooks/post-vault-write.py` — indexa cada `.md` salvo, rate-limited a 1 sinal / 5 s por vault.
- **Biblioteca core** (`core/` na raiz + cópias em `plugins/{core,extended}/core/` para self-contained): paths, db, parser, scanner, frontmatter, regexes, git, i18n, migrations.
- **CLI `sdlc-kit`** expõe: `init-db`, `scan`, `rebuild-db`, `status`, `version`.
- **SQLite** em `.sdlc-kit/db.sqlite` (modo WAL); schema versionado via migrations idempotentes. Perder o DB é recuperável via `sdlc-kit rebuild-db`.

### Contrato comum das skills

Toda skill autora (adr, prd, epic, milestone, spec, trd, review, task, domain, design-system) implementa três ações:

- **`list`** — enumeração read-only.
- **`scaffold` / `new`** — copia template para o local certo; recusa overwrite sem `--force`.
- **`transition`** — flipa o campo `status:` (ou `decision:`) ao longo de um lifecycle definido; idempotente.

Cada script emite um único objeto JSON em stdout. Exit codes: `0` sucesso ou dry-run, `1` erro do usuário, `2` fatal.

### Extensão

Para adicionar uma skill nova:

1. Desenhe triggers (inglês + pt-BR), personas e lifecycle.
2. Scaffold `plugins/{core,extended}/skills/sdlc-<nome>/` com `SKILL.md` + `scripts/<nome>.py`.
3. Respeite o contrato: JSON stdout, exit codes `0|1|2`, `--dry-run` obrigatório em mutações.
4. Registre o type em `sync.py` (`REQUIRED_FIELDS_BY_TYPE`, `VALID_STATUS_BY_TYPE`).
5. Adicione testes em `tests/test_<nome>_skill.py` usando os helpers em `tests/_skill_helpers.py`.
