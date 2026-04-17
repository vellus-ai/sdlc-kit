# SDLC Kit — Claude Code Plugin

Plugin standalone para criar e manter um vault Spec-Driven Development dentro de repositórios Git.

## Regras
- Nunca commitar direto na main; usar `feat/<slug>` / `fix/<slug>`
- TDD: escrever o teste antes da implementação
- Scripts em `skills/` sempre suportam `--dry-run` e emitem JSON no stdout
- Cobertura mínima: 90% nos módulos `core/`

## Worktrees
- Localização: `.worktrees/<branch-slug>`
- Ignorado pelo git (ver .gitignore)
