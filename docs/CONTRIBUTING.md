# Contributing to SDLC Kit

> 📖 **Também disponível em [Português (Brasil)](#contribuindo--português-brasil) abaixo.**

Thanks for your interest in improving the SDLC Kit plugin. This document describes the engineering contract every change must honor: branching, commits, testing, and how to add a new skill.

## Ground rules

- **Language policy.** All code, SKILL.md files, templates, and docs are written in English. The LLM mirrors the user's chat language at runtime — see [ADR-0004](decisions/ADR-0004-i18n-strategy.md).
- **Local-first.** No network calls at scaffold or scan time. Users pick their own backup/sync strategy.
- **Stdlib-first.** `core/` uses only the Python standard library where possible. Optional dependencies live behind extras in `pyproject.toml`.
- **Idempotency.** Every skill script must be safe to re-run. `--dry-run` is the default answer to "what will this change?".

## Branching model

1. Pull the latest `main` and verify a clean working tree.
2. Create a branch with the prefix `claude/` followed by a Conventional Commits type and a short slug:
   - `claude/feat/<slug>` — new capability
   - `claude/fix/<slug>` — bug fix
   - `claude/refactor/<slug>` — behavior-preserving cleanup
   - `claude/docs/<slug>` — documentation only
   - `claude/test/<slug>` — tests only
3. Prefer a `git worktree` (e.g., `.worktrees/<slug>`) so `main` stays clean while you work.
4. Never commit feature work directly on `main`.

## Conventional Commits

Every commit subject follows the [Conventional Commits 1.0](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>
```

Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`. Scope is usually the skill slug (e.g., `adr`, `spec`, `sync`) or `core` for library changes. Subjects are imperative, lowercase, and under 72 characters.

Breaking changes add a `!` after the type and a `BREAKING CHANGE:` footer. Commits that touch user-facing behavior include a short body explaining the why.

## TDD is mandatory

Every change follows red → green → refactor:

1. Write a failing test that asserts the new behavior.
2. Run the test suite and confirm the red.
3. Implement the minimum change that turns it green.
4. Refactor with tests green.
5. Commit.

Test files live under `tests/` mirroring the layout of the production code. Skill tests go in `tests/test_<skill>_skill.py`; core library tests go in `tests/test_<module>.py`.

## Property-based testing (PBT)

Where a rule is easier to state than enumerate, reach for [Hypothesis](https://hypothesis.readthedocs.io/). Good PBT candidates in this codebase:

- Slug validators — every generated slug must round-trip through the regex.
- Frontmatter parsers — any input that looks like valid YAML frontmatter must parse without raising.
- Idempotent transitions — `transition(transition(x, s), s) == transition(x, s)` for every status `s`.
- MOC regenerators — running the generator twice must produce byte-identical output.

Mark PBT tests with `@pytest.mark.pbt` so they can be filtered in CI.

## Coverage ≥ 90% on changed packages

We enforce a floor of 90% branch coverage on any package touched by a PR. See [ADR-0003](decisions/ADR-0003-test-strategy-tdd-pbt.md) for the rationale.

Measure locally:

```bash
pytest --cov=core --cov=skills --cov=hooks --cov-branch --cov-report=term-missing
```

For an HTML report:

```bash
pytest --cov=core --cov=skills --cov=hooks --cov-report=html
open htmlcov/index.html
```

Skip the slow ML model loads during fast iteration:

```bash
pytest -m "not slow"
```

Run only property-based tests:

```bash
pytest -m pbt
```

## Adding a new skill

1. **Design first.** Open an issue or draft a short design note covering the skill's trigger phrases (English + pt-BR), persona(s), lifecycle, output contract, and guardrails.
2. **Scaffold the directory:**
   ```
   skills/sdlc-<name>/
   ├── SKILL.md
   ├── scripts/
   │   └── <name>.py
   ├── references/         (optional — context docs the LLM reads before acting)
   └── assets/             (optional — templates or static files)
   ```
3. **Write SKILL.md in the canonical format** (see `skills/sdlc-domain/SKILL.md`):
   - YAML frontmatter with `name:` and multi-line `description: |`
   - Sections: `What this is (and isn't)`, `When to invoke / When NOT to invoke`, `Flow`, `Output contract`, `Guardrails (Never / Always)`, `Examples`
   - Declare the persona(s) — single lens / duo / triad — explicitly in the description
4. **Write the script** following the contract:
   - Single JSON object on stdout, diagnostics to stderr
   - Exit codes: `0` success/dry-run, `1` user error, `2` fatal
   - Support `--dry-run` for any mutating action
   - Errors appended to `.sdlc-kit/<skill>-errors.log`
5. **Add tests.** Start with `tests/test_<name>_skill.py` using `tests/_skill_helpers.py`. See [TESTING.md](TESTING.md).
6. **Register in `sync.py`.** Add the new `type` value to `REQUIRED_FIELDS_BY_TYPE` and `VALID_STATUS_BY_TYPE` so the librarian validates its frontmatter.
7. **Register in the plugin manifest.** Append the skill entry to `.claude-plugin/plugin.json`.
8. **Run the full suite:** `pytest --cov` and confirm coverage ≥ 90% on changed packages.

## Pull request checklist

Before opening a PR:

- [ ] Branch is `claude/<type>/<slug>` and rebased on latest `main`
- [ ] Every commit follows Conventional Commits
- [ ] Tests added/updated; `pytest` passes locally
- [ ] Coverage ≥ 90% on any package you modified
- [ ] `ruff check .` and `mypy core skills hooks` are clean
- [ ] No secrets or absolute paths committed
- [ ] `CHANGELOG.md` updated under `## Unreleased` when the change is user-visible

Open the PR with `gh pr create`, referencing any related ADR or issue in the description.

---
---

## Contribuindo — Português (Brasil)

> A versão canônica é a **inglesa acima**. Esta seção resume o essencial em português.

Obrigado pelo interesse em melhorar o plugin SDLC Kit.

### Regras

- **Política de idioma.** Todo código, SKILL.md, templates e docs em inglês. O LLM espelha o idioma do chat em tempo de execução — ver [ADR-0004](decisions/ADR-0004-i18n-strategy.md).
- **Local-first.** Sem chamadas de rede no scaffold ou scan.
- **Stdlib-first.** `core/` usa apenas a stdlib Python quando possível. Dependências opcionais ficam atrás de extras no `pyproject.toml`.
- **Idempotência.** Todo script de skill deve ser seguro de re-executar. `--dry-run` é a resposta default.

### Branch e commits

1. Puxe `main` atualizado, verifique working tree limpo.
2. Crie branch com prefixo `claude/` + tipo Conventional Commits + slug:
   - `claude/feat/<slug>` — nova capacidade
   - `claude/fix/<slug>` — correção
   - `claude/refactor/<slug>` — refactoring sem mudança de comportamento
   - `claude/docs/<slug>` — docs
   - `claude/test/<slug>` — testes
3. Prefira um `git worktree` (ex: `.worktrees/<slug>`) para manter `main` limpo.
4. Nunca commite feature work direto na `main`.

### Conventional Commits

Formato `<type>(<scope>): <subject>` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, etc.

### Adicionando uma skill nova

1. Desenhe triggers (EN + pt-BR), personas, lifecycle.
2. Scaffold `plugins/{core,extended}/skills/sdlc-<nome>/` com `SKILL.md` + `scripts/<nome>.py`.
3. Respeite o contrato: JSON stdout, exit codes `0|1|2`, `--dry-run` obrigatório em mutações.
4. Registre em `sync.py` (`REQUIRED_FIELDS_BY_TYPE`, `VALID_STATUS_BY_TYPE`).
5. Adicione testes em `tests/test_<nome>_skill.py`.

### Antes de abrir PR

- [ ] `pytest` passa (todos os testes verdes)
- [ ] `ruff check .` e `mypy core plugins tests` limpos
- [ ] Sem segredos ou caminhos absolutos commitados
- [ ] `CHANGELOG.md` atualizado em `## Unreleased` se a mudança for user-visible
