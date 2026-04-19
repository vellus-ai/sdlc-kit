# Publishing SDLC Kit

> 📖 **Também disponível em [Português (Brasil)](#publicando--português-brasil) abaixo.**

How to publish new versions of the plugin to users — both through our own
vendor marketplace (available the instant a tag is pushed) and through the
official Anthropic directory (curated, reviewed).

---

## Audiences and tracks

| Track | Curation | Time to availability | Install command |
|---|---|---|---|
| **A — Vendor marketplace** (this repo) | self-serve | as soon as the tag is pushed | `/plugin marketplace add vellus-ai/sdlc-kit` + `/plugin install sdlc-kit@sdlc-kit` |
| **B — Official Anthropic directory** | reviewed by Anthropic | async (no published SLA) | `/plugin install sdlc-kit@claude-plugins-official` |

Both tracks can run in parallel. **Track A is our canonical install path.**
Track B is a nice-to-have that increases discoverability.

---

## Pre-flight checklist (required for both tracks)

Before cutting any release, every box must be checked:

- [ ] All tests pass locally: `py -m pytest -q -p no:randomly`
- [ ] Coverage gate passes: `py -m coverage combine && py -m coverage report --fail-under=80`
- [ ] Registry audit clean: `py scripts/audit_registry.py` → `status: ok`, no drift
- [ ] Ruff clean: `py -m ruff check core/ skills/ hooks/ tests/ scripts/`
- [ ] `CHANGELOG.md` has an entry for the new version (not `[Unreleased]`)
- [ ] `README.md` mentions the correct version in the badge
- [ ] No dead references: `grep -rn "sdlc-kit:sprint\|sdlc-kit:tasks" --include="*.md"` returns zero
- [ ] `.claude-plugin/plugin.json` has the new version
- [ ] `.claude-plugin/marketplace.json` has the same version
- [ ] `pyproject.toml` has the same version (use `py scripts/bump_version.py X.Y.Z` to sync all four)
- [ ] Plugin validates: `claude plugin validate .` (if you have the Claude Code CLI installed locally)

**Version duplication trap** — never set `plugins[0].version` inside
`marketplace.json`. `plugin.json:version` silently wins when both are
present; users stay stuck on a stale release. The bump script
(`scripts/bump_version.py`) already leaves the marketplace entry's version
absent.

---

## Track A — vendor marketplace (this repo)

Every push of a tag `vX.Y.Z` triggers the `release.yml` workflow, which:
1. Verifies version coherence across `pyproject.toml`, `plugin.json`,
   `marketplace.json`, and the README badge.
2. Extracts the `[X.Y.Z]` section of `CHANGELOG.md` as release notes.
3. Publishes the GitHub Release.

### Release steps

```bash
# 1. Bump atomically
py scripts/bump_version.py 0.3.0

# 2. Migrate Unreleased → [0.3.0] — YYYY-MM-DD in CHANGELOG.md (manual)

# 3. Commit + push + tag
git add -A
git commit -m "chore(release): 0.3.0"
git push origin main

git tag -a v0.3.0 -m "Release v0.3.0 — <one-liner>"
git push origin v0.3.0

# 4. Verify
gh release view v0.3.0 --repo vellus-ai/sdlc-kit
gh run list --workflow=release.yml --limit 1
```

### User install (announce in README)

```
/plugin marketplace add vellus-ai/sdlc-kit
/plugin install sdlc-kit@sdlc-kit
/reload-plugins
```

Users can pin a specific release:

```
/plugin marketplace add vellus-ai/sdlc-kit@v0.3.0
```

### Updates

`vellus-ai/sdlc-kit` is a **third-party marketplace** — Claude Code does
**not** auto-update installed plugins from it. Users must re-run:

```
/plugin marketplace update sdlc-kit
```

Communicate major version bumps via the GitHub Release notes and a ping
on whatever channel your users follow.

---

## Track B — official Anthropic directory

Anthropic runs a curated directory at
[`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official).
It is pre-registered in every Claude Code install, so listed plugins are
installable without a marketplace-add step.

### Submission

There is **no public PR, issue, or fork flow** — the process goes through
an authenticated in-app form:

- [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
- [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)
- Short URL: [clau.de/plugin-directory-submission](https://clau.de/plugin-directory-submission)

Log in as a Vellus maintainer, fill the form (plugin name, repo URL,
description, category, security/trust attestations), and submit.

### What Anthropic reviews

1. **Automated review** — pre-listing. Scope not publicly documented.
2. **Anthropic Verified badge** (optional) — separate, higher-bar manual
   quality + security review.

There is **no published SLA**, no public rubric, no public list of
required attestations. Treat Track B as asynchronous and do not block
releases on it.

### After acceptance

The plugin appears in `claude-plugins-official/marketplace.json`
automatically (maintained by Anthropic). Users can install via:

```
/plugin install sdlc-kit@claude-plugins-official
```

---

## Reserved names (avoid)

Claude.ai marketplace sync rejects names that impersonate official
marketplaces or look like ambiguous Anthropic brand extensions:

- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`
- `agent-skills`
- `knowledge-work-plugins`
- `life-sciences`
- any `anthropic-*` / `claude-*` variant that impersonates first-party

Our marketplace name is `sdlc-kit` (kebab-case, vendor-scoped) — safe.

---

## Security and trust hygiene

Ship these guarantees in every release:

1. **No hardcoded secrets** — `.claude-plugin/` and scripts are plain text,
   cached under `~/.claude/plugins/cache/` which is user-readable.
2. **Paths via env vars** — hooks and scripts use
   `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`, never absolute paths.
3. **Hooks executable with safe shebangs** — `hooks/*.py` starts with
   `#!/usr/bin/env python3`.
4. **No path traversal** — nothing in the plugin references `../` outside
   its own directory.
5. **License is SPDX** — `license: "MIT"` in both manifests.
6. **`.gitignore` excludes local coverage data and worktrees** so nothing
   private ships inadvertently.

Anthropic explicitly disclaims verification of plugin contents — the
burden of proof is on the publisher. Expect scrutiny during the Track B
review.

---

## FAQ

**Can I submit via a PR to `anthropics/claude-plugins-official`?**
No. The curated directory only accepts submissions via the authenticated
in-app form.

**Do users need to install both tracks?**
No. They pick one. The vendor marketplace (Track A) and the official
directory (Track B) are alternative install paths; installing the plugin
twice under different marketplace names causes name collision.

**How do I push a hotfix?**
Bump the patch version (e.g., `0.3.1`), run the release steps in Track A.
For Track B, there is no fast-lane — the next automated review picks up
the new tag.

**Can I publish a private release?**
Yes, from a private GitHub repo. Users must have `GITHUB_TOKEN` in their
environment when they run `/plugin marketplace add`. The official
directory only accepts public repos.

---

## External references

- [Create plugins (Claude docs)](https://code.claude.com/docs/en/plugins)
- [Create and distribute a plugin marketplace (schema)](https://code.claude.com/docs/en/plugin-marketplaces)
- [Discover and install prebuilt plugins](https://code.claude.com/docs/en/discover-plugins)
- [Plugins reference (manifest schema)](https://code.claude.com/docs/en/plugins-reference)
- [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official)
- [claude.ai plugin submission form](https://claude.ai/settings/plugins/submit)

---
---

## Publicando — Português (Brasil)

> A versão canônica é a **inglesa acima**. Esta seção resume o essencial em português.

### Tracks de publicação

| Track | Curadoria | Tempo até disponibilidade | Comando de instalação |
|---|---|---|---|
| **A — Vendor marketplace** (este repo) | self-serve | assim que a tag é pushed | `/plugin marketplace add vellus-ai/sdlc-kit` + `/plugin install sdlc-kit@sdlc-kit` |
| **B — Diretório oficial Anthropic** | revisão Anthropic | async (sem SLA publicado) | `/plugin install sdlc-kit@claude-plugins-official` |

Ambos tracks podem rodar em paralelo. **Track A é nosso caminho canônico de instalação.** Track B é bônus de descoberta.

### Pre-flight checklist (obrigatório nos dois tracks)

Antes de cortar qualquer release, todo item deve estar marcado:

- [ ] Todos os testes passam localmente: `py -m pytest -q -p no:randomly`
- [ ] Gate de cobertura passa: `py -m coverage combine && py -m coverage report --fail-under=80`
- [ ] Auditoria de registry limpa: `py scripts/audit_registry.py` → `status: ok`, sem drift
- [ ] Ruff limpo: `py -m ruff check core/ plugins/ tests/ scripts/`
- [ ] `CHANGELOG.md` tem entrada para a nova versão (não `[Unreleased]`)
- [ ] `README.md` cita a versão correta no badge
- [ ] Sem referências mortas: `grep -rn "sdlc-kit:sprint\|sdlc-kit:tasks" --include="*.md"` retorna zero
- [ ] `plugins/core/.claude-plugin/plugin.json` e `plugins/extended/.claude-plugin/plugin.json` têm a nova versão
- [ ] `.claude-plugin/marketplace.json` declara os 2 plugins
- [ ] `pyproject.toml` tem a mesma versão

### Tag e push

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z — <highlight>"
git push origin vX.Y.Z
```

O `.github/workflows/release.yml` lê a seção do CHANGELOG da tag e cria a GitHub Release automaticamente.

### Submissão ao diretório oficial Anthropic

Faça login como mantenedor Vellus, preencha o formulário ([`claude.ai/settings/plugins/submit`](https://claude.ai/settings/plugins/submit)) com nome do plugin, URL do repositório, categoria. A revisão é assíncrona.
