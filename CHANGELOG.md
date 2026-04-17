# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
aderindo ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-04-17

### Adicionado

#### Core
- `core/paths.py` — descoberta do vault por caminhamento de ancestrais (`.sdlc-kit/marker.json`)
- `core/db.py` — conexão SQLite com modo WAL, FK constraints, migrations idempotentes
- `core/migrations/001_initial.sql` — 7 tabelas: `notes`, `events`, `links`, `tasks`, `decisions`, `worktrees`, `schema_version`
- `core/parser.py` — extração de frontmatter YAML e wikilinks `[[...]]` (stdlib puro, PyYAML opcional)
- `core/scanner.py` — varredura delta por mtime, upsert na tabela `notes`
- `core/git.py` — `parse_worktree_list`, `parse_pr_list`, `sync_worktrees` (integração com `gh pr list`)
- `core/cli.py` — comandos `init-db`, `scan`, `status`

#### Hook
- `hooks/post-vault-write.py` — PostToolUse hook para Write/Edit/NotebookEdit; rate-limited (1 sinal/5s); degrada graciosamente se SQLite indisponível

#### Assets
- `assets/vault-tree/` — templates para todas as 7 fases do vault
- `assets/vault-tree/dashboard.html` — dashboard autocontido com File System Access API, 4 abas: Tasks (Kanban + Branch Graph), Épicos & Milestones, Documentos (markdown renderer), Domínio
- `assets/vault-tree/CLAUDE.md.tpl` — doutrina do vault com schema de frontmatter
- `assets/vault-tree/_INDEX.md.tpl` — índice vivo do vault

#### Skills — Fase 1 (Fundação)
- `/sdlc-kit:init` — scaffold idempotente com entrevista de 7 perguntas
- `/sdlc-kit:sync` — validação de frontmatter, atualização de MOCs e `_INDEX.md`
- `/sdlc-kit:status` — resumo JSON de saúde do vault
- `/sdlc-kit:steer` — merge seguro de seções no `CLAUDE.md` do vault

#### Skills — Fase 2 (SDD Core)
- `/sdlc-kit:spec` — trio SDD: `requirements.md` (EARS) + `design.md` + `tasks.md`
- `/sdlc-kit:prd` — Product Requirements Document com numeração automática
- `/sdlc-kit:adr` — Architecture Decision Record com numeração automática (ADR-NNN)
- `/sdlc-kit:doc` — documento genérico a partir de template configurável

#### Skills — Fase 3 (Entrega)
- `/sdlc-kit:epic` — criação e listagem de épicos em `EPICS.md` (append-only)
- `/sdlc-kit:milestone` — milestones com RAG status calculado (Red/Amber/Green)
- `/sdlc-kit:task` — add/list/update-status em `TASKS.md`; suporte a `[EPIC]` e `@branch`
- `/sdlc-kit:review` — checklist: spec trios, frontmatter, TASKS.md, ADRs não travados

#### Skills — Fase 4 (DDD + Arquitetura)
- `/sdlc-kit:domain` — bounded context: `context-map.md` + `ubiquitous-language.md` + `domain-events.md`
- `/sdlc-kit:c4` — diagramas C4 em Mermaid: Context, Container e Component
- `/sdlc-kit:design-system` — tokens, componentes e padrões de design
- `/sdlc-kit:trace` — matriz de rastreabilidade: EARS requirements → tasks
- `/sdlc-kit:impact` — análise de impacto de conceito/termo no vault inteiro

#### Skills — Fase 5 (Ciclo Completo)
- `/sdlc-kit:worktree` — ciclo completo: create/list/close/sync de git worktrees
- `/sdlc-kit:retro` — retrospectivas com seções padrão e itens de ação rastreáveis

#### Plugin
- `.claude-plugin/plugin.json` — manifest com hook PostToolUse + registro das 19 skills
- `pyproject.toml` — pacote Python instalável, entry point `sdlc-kit`

#### Testes
- 130 testes cobrindo core, todas as skills e integração

[0.1.0]: https://github.com/vellus-ai/sdlc-kit/releases/tag/v0.1.0
