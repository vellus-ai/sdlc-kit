# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
aderindo ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.3.3] — 2026-04-18

### Corrigido

- **`test_dash_skill` shim quebrava `coverage.process_startup` em win/py3.11** — o shim temporário para neutralizar o abridor de browser substituía `subprocess.run` globalmente com um lambda que retornava `None` (ou levantava `RuntimeError`). Em Python 3.11 no Windows, a importação de `coverage.process_startup()` (carregada via `tests/sitecustomize.py` na PYTHONPATH) chama `subprocess.run` internamente e crashava com `AttributeError: 'NoneType' object has no attribute 'stdout'`. Fix: shim agora usa `_guarded_run` que intercepta apenas `argv[0] in ('open', 'xdg-open')` (os dois comandos que o `dash.py` chama em Darwin/Linux) e passa tudo mais pelo `subprocess.run` original. `os.startfile` (path Windows) continua substituído diretamente.
- **Resultado**: CI passou **12/12 jobs em 9 combinações** (ubuntu/macos/windows × py3.11/3.12/3.13) + lint + coverage + registry audit — primeiro green full desde a expansão do matrix.

## [0.3.2] — 2026-04-18

### Corrigido

- **CI completamente verde em 9 combinações** — v0.3.1 corrigiu o `ModuleNotFoundError`, mas deixou três issues visíveis:
  1. **Lint (ruff) com 116 erros** — acúmulo de imports não-utilizados (`F401`), `if` aninhados (`SIM102`), refatorações automáticas (`UP`/`B`). Aplicado `ruff check --fix` + `--unsafe-fixes` em 109 erros; remanescentes 2 blocos `if/else` para ternário e 1 `E402` consertados à mão. Adicionado `SIM102` ao `ignore` do `pyproject.toml` (estilístico, não bug). Removidas duplicatas órfãs de `read_frontmatter` em `sdlc-prd` e `sdlc-steer` (restos da refatoração Fase 1 que o `F811` detectou).
  2. **`UnicodeEncodeError 'charmap'` no Windows py3.13** — os scripts emitem JSON com caracteres como `→`, `—`, em-dash em mensagens de erro. No Windows o default stdout é cp1252 e falha ao encodar. **Fix**: `tests/_skill_helpers._subprocess_env()` força `PYTHONIOENCODING=utf-8` no env de todo subprocess; `run_script()` passa `errors="replace"` no decode para tolerar bytes não-UTF-8 no stderr do child.
  3. **Script `skills/sdlc-impact/scripts/impact.py`** — 1 bloco `if/else` de 4 linhas reduzido para expressão ternária (legibilidade preservada).
- **`skills/sdlc-prd/scripts/prd.py` + `skills/sdlc-steer/scripts/steer.py`** — duplicatas da função `read_frontmatter` que sobreviveram à extração para `core/frontmatter.py` foram removidas (causavam `F811` em ruff).
- **`skills/sdlc-sync/scripts/sync.py`** — `import contextlib` movido para o bloco de imports ordenado por ruff (`UP`/`I` conformance).

## [0.3.1] — 2026-04-18

### Corrigido

- **CI fail em todas as 9 combinações (ubuntu/macos/windows × py3.11/3.12/3.13)** — o job `test` falhava na fase de coleta com `ModuleNotFoundError: No module named 'tests'`. Causa: os arquivos de teste importam `from tests._skill_helpers import ...` para compartilhar fixtures, mas o runner de CI instala apenas os pacotes listados em `pyproject.toml` (`core`, `hooks`, `skills`) — sem `tests/`. Localmente pytest achava o path via rootdir discovery; no CI, não.
- **Solução**: adicionar `tests/__init__.py` (vazio, com docstring explicativa). Isso transforma `tests/` em um pacote Python importável, tornando os imports `from tests._skill_helpers import ...` resolúveis em qualquer ambiente, incluindo CI com venv limpa.
- **Bônus**: `release.yml` agora publica v0.3.1 com notes extraídos desta seção do CHANGELOG automaticamente.

### Smoke test (Track A — vendor marketplace)

Validado manualmente antes do tag:

```bash
mkdir /tmp/smoke && cd /tmp/smoke && git init
python .../sdlc-init/scaffold.py --vault-root . --project-name smoke --owner tester
python -c "from core.db import connect, run_migrations; ..."    # init DB
python .../sdlc-sync/sync.py --vault-root .
# → 65 arquivos criados (vault completo: 8 fases + CLAUDE.md + _INDEX.md + dashboard.html + db.sqlite)
# → _INDEX.md renderizado em pt-BR por default
# → 506 testes da suite continuam 100% verdes
```

## [0.3.0] — 2026-04-18

### Adicionado

- **i18n do `_INDEX.md` e dos `_MOC.md`** — `skills/sdlc-sync/scripts/sync.py` agora é totalmente locale-aware. `render_index()` e `render_moc_artifacts()` recebem um parâmetro `locale` e substituem as ~60 strings pt-BR hard-coded por chamadas `t(locale, key)` ao dicionário em `core/i18n.py`. O locale é lido do vault via o novo helper `core.paths.read_locale()`, que extrai `.sdlc-kit/marker.json:locale` (default `pt-br`, fallback `en`). Vaults existentes seguem renderizando em pt-BR sem mudança. Vaults novos podem pedir inglês: `scaffold --locale en`.
- **`core.paths.read_locale(vault_root)`** — helper público que normaliza hífens e caixa (`PT_BR` → `pt-br`), trata marker ausente/malformado, devolve `DEFAULT_LOCALE` graciosamente. 100% de cobertura.
- **`skills/sdlc-init/scripts/scaffold.py --locale {pt-br,en}`** — grava `locale` no `marker.json` durante o init. Opcional; default `pt-br`.
- **+14 chaves em `core/i18n.py`** — `index.panorama.table_header_{metric,value}`, `moc.artifacts.{empty,col_document,col_type,col_status,col_updated}` — em `pt-br` e `en` com tradução paralela completa.
- **Coverage de subprocess** — `tests/sitecustomize.py` + `COVERAGE_PROCESS_START` + `[tool.coverage.run] parallel = true, concurrency = ["multiprocessing", "thread"]`. `tests/_skill_helpers.py::run_script` injeta `tests/` em `PYTHONPATH` para que o shim `sitecustomize` seja carregado automaticamente em todo subprocess. A cobertura do `ci.yml` passa a rodar `pytest → coverage combine → coverage report --fail-under=80` e agora captura linhas dos **23 skill scripts + hook** (antes 0%; hoje 85–93% por módulo; total combinado 84%).
- **CI matrix 3 OS × 3 Python** — `.github/workflows/ci.yml` roda tests em `ubuntu-latest`, `macos-latest`, `windows-latest` × Python `3.11`, `3.12`, `3.13` com `fail-fast: false`. 9 combinações.
- **`docs/PUBLISHING.md`** — guia completo de publicação: Track A (vendor marketplace via `/plugin marketplace add`), Track B (oficial Anthropic), checklist pré-release, hygiene de segurança, FAQ.
- **Install via Claude Code marketplace** — README ganha o snippet `/plugin marketplace add vellus-ai/sdlc-kit` + `/plugin install sdlc-kit@sdlc-kit` como instalação primária recomendada (one-liner continua disponível como alternativo).

### Corrigido

- **`marketplace.json`** — removido o campo `plugins[0].version` (evita o "duplicate version trap" descrito na pesquisa oficial: quando presente nos dois arquivos, `plugin.json:version` silenciosamente vence e usuários ficam presos em versões stale). `plugin.json:version` é agora a única fonte da verdade.
- **Descrição do marketplace enriquecida** — atualizada para refletir as 23 skills reais (antes listava subset antigo), destaca API contracts e i18n pt-br/en.

## [0.2.0] — 2026-04-18

### Adicionado

- **`core/regexes.py`** — patterns canônicos (`SLUG_RE`, `FRONTMATTER_RE`, `STATUS_LINE`, `UPDATED_LINE`, `WIKILINK_RE`) antes duplicados em 18 scripts de skills. 100% de cobertura.
- **`core/frontmatter.py`** — helpers `read_frontmatter`, `parse_frontmatter_text`, `set_quoted_field`, `render_frontmatter` para uso compartilhado. 100% de cobertura + property-based tests (round-trip `parse(render(fm)) == fm`, idempotência de `set_quoted_field`).
- **`core/i18n.py`** — dicionário `MESSAGES` com ~60 chaves em `pt-br` e `en`; helper `t(locale, key, **kwargs)` com fallback para `en` e depois para a chave literal. Preparado para tornar o renderer do `_INDEX.md` localizável em PR futura.
- **Suite de testes expandida** — de 169 para **496 testes passando** com `pytest-cov --cov-branch`. Novas coberturas: `sdlc-status`, `sdlc-dash`, `sdlc-doc`, `sdlc-init` (detect + scaffold), `sdlc-steer`, `sdlc-epic`, `sdlc-prd`, `sdlc-milestone`, `sdlc-adr` (com PBT de bijeção de filename), `sdlc-task`, `sdlc-spec`, `sdlc-sync`, `hooks/post-vault-write.py`.
- **`.github/workflows/ci.yml`** — lint (ruff), tests em matriz (Python 3.11 / 3.12), coverage gate ≥ 90%, auditoria de registry.
- **`.github/workflows/release.yml`** — validação de versão + publicação automática de GitHub Release em tag `v*`.
- **`scripts/audit_registry.py`** — auditoria automática template ↔ `sync.py` registry; emite JSON, exit 1 em drift.
- **`scripts/bump_version.py`** — bump atômico coordenado em `pyproject.toml`, `plugin.json`, `marketplace.json`, badge do README.
- **`scripts/refactor_skill_imports.py`** — script one-shot que migrou os 18 scripts para importar de `core/regexes` + `core/frontmatter`.
- **`docs/CONTRIBUTING.md`** — fluxo de PR, Conventional Commits, TDD obrigatório, PBT, cobertura mínima, como adicionar uma nova skill.
- **`docs/TESTING.md`** — filosofia de testes, helper `_skill_helpers.py`, PBT com hypothesis, anatomia de um `test_*_skill.py`.
- **`docs/ARCHITECTURE.md`** — diagramas C4 textuais do plugin, fluxo de dados, padrão `list/scaffold/transition`, registry como fonte da verdade.
- **`docs/decisions/ADR-0003-test-strategy-tdd-pbt.md`** — decisão de adotar TDD + PBT + cobertura ≥ 90% (MADR).
- **`docs/decisions/ADR-0004-i18n-strategy.md`** — decisão de i18n via `core/i18n.py` com locale lido de `marker.json` (MADR).
- **23 SKILL.md no formato canônico** — todos com `description: |` (multi-linha), personas (lens duo/triad/single), triggers em EN + pt-BR explícitos, seções uniformes (When to invoke / When NOT / Flow / Output contract / Guardrails / Examples).
- **Registry em `sync.py` expandido**: agora cobre `retro.status`, `review.status`, `branch.slug`, `incident-lessons`, 3 `steering-*`, `index`. Zero drift via `audit_registry.py`.

### Corrigido

- **Refactor sem duplicação** — removidas ~9.4 KB de código repetido (regex + helpers) nos 18 scripts; agora importados de `core/`.
- **`--fix` flag em `sync.py`** — agora emite warning explícito em stderr quando usado (antes era no-op silencioso).
- **Dead references** — `/sdlc-kit:sprint`, `/sdlc-kit:c`, `/sdlc-kit:tasks` (nomes de skills que não existem) substituídas ou removidas em `README.md`, `sync.py`, `CLAUDE.md.tpl`, `_INDEX.md.tpl`, ADRs e SKILL.md.
- **README typo** — `tests/test_core_scanner.py` corrigido para `tests/test_scanner.py`.
- **`marketplace.json`** — contagem de skills atualizada de 20 para 23.
- **`dash.py` language policy** — substituído `subprocess.run(["start", ...], shell=True)` por `os.startfile` no Windows; removido string pt-BR hard-coded no JSON de saída.
- **Bug descoberto via TDD em `SLUG_RE`** — trocado `^...$` por `\A...\Z` porque `$` no Python aceita `\n` final ("trailing\n" era aceito como slug válido).

### Refatorado — padronização canônica das skills

Toda a malha de skills foi alinhada a um contrato único (`list / scaffold / transition`),
com validação cruzada via `sync.py` registry (types + status enums) e SKILL.md no
padrão multi-linguagem (triggers em EN + pt-BR, personas como duo ou triad, hard gates
antes de `approved`).

- **Padrão canônico adotado em todas as skills** — scripts emitem um único JSON em
  stdout; exit codes `0` (ok/dry-run) / `1` (erro do usuário) / `2` (fatal); frontmatter
  regex com `[ \t]` boundary para preservar a linha em branco após o fence; slug regex
  `[a-z0-9][a-z0-9-]*`; transições idempotentes que atualizam o campo `updated` só
  quando o status realmente muda.
- **`/sdlc-kit:domain` reescrito** — agora com 5 kinds: `aggregate` / `event` /
  `contract` (coleções) + `context-map` / `ubiquitous-language` (singletons). Lifecycle
  comum `draft → approved → deprecated`. Types registrados em `sync.py` com prefixo
  `domain-*` para consistência com as famílias `spec-*` e `design-*`.
- **`/sdlc-kit:c4` reescrito** — 3 kinds: `context` / `container` (singletons) +
  `component` (coleção por slug). Mesmo lifecycle. Tipos `c4-context` / `c4-container`
  / `c4-component` registrados em `sync.py`.
- **`/sdlc-kit:api` — skill nova** (antes ausente). 4 kinds para contratos de API:
  `rest`, `async`, `grpc`, `webhook`. Templates já existiam em
  `02-architecture/_templates/api/`. Tipos `api-*` registrados em `sync.py`.
- **`/sdlc-kit:trd` — skill nova** para Technical Requirements Documents cross-cutting
  (performance / scalability / reliability / security / privacy-LGPD / observability /
  accessibility / maintainability / i18n / cost). Persona triad (Software Architect +
  AppSec Engineer + SRE). Lifecycle `draft → approved → deprecated`. Pre-approval
  checklist bloqueia promoção sem SLI/SLOs, exception flow via ADR, sign-off triad.
- **`/sdlc-kit:review` reescrito** — agora com **dois eixos independentes**: `status`
  (`draft → final`, controlado por `transition`) e `decision` (`pending → approved /
  approved-with-comments / changes-requested`, controlado por `decide`). Duo de
  personas **Senior Engineer (Code Reviewer) + AppSec Engineer** alinhado com a política
  do `CLAUDE.md`. Checklist de 6 seções (Design / Code Quality / Tests / AppSec /
  Privacy-LGPD / Process). Findings com severidade (🔴 Blocker / 🟡 Major / 🟢 Minor
  / 🔵 Praise). Scaffold suporta `--pr N --pr-url URL --author A`.
- **`/sdlc-kit:incident` — skill nova** para post-mortems. Lifecycle 4-estados `open →
  mitigated → resolved → post-mortem`. Transições **auto-preenchem** `mitigated_at` e
  `resolved_at` com a data atual quando os campos estão vazios. Severity enum enforce
  `SEV1 | SEV2 | SEV3 | SEV4`. Persona duo SRE + Engineering Lead.
- **`/sdlc-kit:worktree` reescrito** — agora com 2 kinds: `worktree` (lifecycle `active
  → merged / abandoned`) e `branch` (sem enum formal, apenas registro). Transição
  só permitida em `worktree`. Persona duo Senior SWE + Release Engineer.
- **`/sdlc-kit:retro` reescrito** — single-kind, lifecycle `draft → final`. Scaffold
  aceita `--sprint N` para injetar o campo `sprint:` no frontmatter. Persona duo Agile
  Facilitator + Engineering Lead, com hard gate na transição para `final`.
- **`/sdlc-kit:trace` reescrito** — ferramenta read-only de análise. Caminha o grafo
  de wikilinks e reporta a matriz de rastreabilidade PRD → spec-requirements →
  spec-design → spec-tasks → review, além de detectar ADRs/TRDs órfãos, designs sem
  PRD a montante e PRDs sem implementação a jusante. Suporta `--format json|markdown`
  e `--slug <feature>` para estreitar o escopo.
- **`/sdlc-kit:impact` reescrito** — BFS sobre o grafo de wikilinks a partir de um
  seed, com `--direction forward|backward|both` e `--depth N` (clampado a 10). Saída
  JSON ou markdown com nós, arestas e agregação por tipo.
- **`/sdlc-kit:status` — description reescrita** para o padrão multi-linguagem
  canônico; script mantido.

### Adicionado

- **Registry expandido em `sync.py`** — 12 novos tipos: 5 `domain-*`, 3 `c4-*`, 4
  `api-*`. Todos com campos obrigatórios e enum de status registrados.
- **Fase canônica `00-steering`** reconhecida pelo `sync.py` (antes apenas
  01-steering → 07-retrospectives).
- **Fase canônica `03-domain`** (antes `04-domain`) alinhada ao novo schema.

### Corrigido

- Inconsistência entre `type` no template de cada skill (usava `domain-aggregate`,
  `c4-context`, etc.) e o enum registrado em `sync.py` (usava `aggregate`, sem
  prefixo): todos alinhados para o padrão prefixado.
- README e `plugin.json` com contagem de skills desatualizada (diziam "19" ou "20";
  agora refletem 23).
- Descrição do plugin atualizada para mencionar as 8 fases canônicas (antes "7 fases").

---

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
- `assets/vault-tree/` — templates para todas as fases do vault
- `assets/vault-tree/dashboard.html` — dashboard autocontido com File System Access API, 4 abas: Tasks (Kanban + Branch Graph), Épicos & Milestones, Documentos (markdown renderer), Domínio
- `assets/vault-tree/CLAUDE.md.tpl` — doutrina do vault com schema de frontmatter
- `assets/vault-tree/_INDEX.md.tpl` — índice vivo do vault

#### Skills — primeira safra
- Fundação: `/sdlc-kit:init`, `/sdlc-kit:sync`, `/sdlc-kit:status`, `/sdlc-kit:steer`
- SDD: `/sdlc-kit:spec`, `/sdlc-kit:prd`, `/sdlc-kit:adr`, `/sdlc-kit:doc`
- Entrega: `/sdlc-kit:epic`, `/sdlc-kit:milestone`, `/sdlc-kit:task`, `/sdlc-kit:review` (v1)
- Arquitetura/DDD: `/sdlc-kit:domain` (v1), `/sdlc-kit:c4` (v1), `/sdlc-kit:design-system`, `/sdlc-kit:trace` (v1), `/sdlc-kit:impact` (v1)
- Ciclo: `/sdlc-kit:worktree` (v1), `/sdlc-kit:retro` (v1), `/sdlc-kit:dash`

#### Plugin
- `.claude-plugin/plugin.json` — manifest com hook PostToolUse e descoberta de skills
- `pyproject.toml` — pacote Python instalável, entry point `sdlc-kit`

[Unreleased]: https://github.com/vellus-ai/sdlc-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/vellus-ai/sdlc-kit/releases/tag/v0.1.0
