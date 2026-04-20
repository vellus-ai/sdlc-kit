# SDLC Kit — Claude Code Plugin

Standalone plugin for creating and maintaining a Spec-Driven Development vault inside Git repositories.

## Rules

- Never commit directly to `main`; use `feat/<slug>` / `fix/<slug>`.
- TDD — write the test before the implementation.
- Scripts under `plugins/*/skills/` always support `--dry-run` and emit JSON on stdout.
- Minimum coverage: 90% on `core/` modules.

## Worktrees

- Location: `.worktrees/<branch-slug>`
- Ignored by git (see `.gitignore`)

---

## Português (Brasil)

Plugin standalone para criar e manter um vault de Spec-Driven Development dentro de repositórios Git.

### Regras

- Nunca commitar direto na `main`; usar `feat/<slug>` / `fix/<slug>`.
- TDD: escrever o teste antes da implementação.
- Scripts em `plugins/*/skills/` sempre suportam `--dry-run` e emitem JSON no stdout.
- Cobertura mínima: 90% nos módulos `core/`.

### Worktrees

- Localização: `.worktrees/<branch-slug>`
- Ignorado pelo git (ver `.gitignore`)

---

## SDLC Vault

Leia [[.sdlc/_INDEX]] antes de iniciar qualquer tarefa.
Doutrina do vault: `.sdlc/CLAUDE.md`
