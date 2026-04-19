---
id: ADR-0004
title: i18n strategy — code in English, UX mirrors user's chat language
status: accepted
date: 2026-04-18
author: Milton Silva Jr.
tags: [i18n, locales, language-policy, ux]
supersedes: []
---

# ADR-0004 — i18n strategy: English artifacts, locale-aware UX via `core/i18n.py`

> 🇧🇷 **Resumo em português:** Esta ADR fixa que código, SKILL.md, templates e docs técnicos são escritos em **inglês** (agnóstico de linguagem). O UX gerado (`_INDEX.md`, `_MOC.md`) é renderizado no idioma definido em `.sdlc-kit/marker.json:locale` (default `pt-br`, alternativo `en`) via `core/i18n.py`. O LLM espelha o idioma da conversa do usuário ao preencher conteúdo narrativo. Status: **aceita**.

## Status

Accepted.

## Context

The SDLC Kit plugin ships from a team that works primarily in Brazilian Portuguese. Early releases reflected that: scaffolded CLAUDE.md was in pt-BR, the librarian emitted pt-BR report strings, and the skill frontmatter mixed English trigger keywords with pt-BR prose. This had two problems:

1. **The plugin is inherently language-agnostic.** It organizes a Git repository's SDLC artifacts. Developers on any team should be able to adopt it regardless of their working language.
2. **Hard-coded language strings block contribution.** An English-speaking contributor has to either contribute in broken pt-BR or refactor every string on their way in.

At the same time, we do not want to strip the plugin of its multilingual charm. Users reporting bugs or running `/sdlc-kit:status` expect the assistant to mirror whatever language they are speaking in chat — that is both more natural and is the pattern established by the user's global `CLAUDE.md` (which instructs the LLM to reply in pt-BR when the user writes in pt-BR).

The question became: where does each language belong?

Three options were considered:

### Option A — Everything in pt-BR, English as an afterthought

The status-quo direction. Rejected: makes external contribution painful, confuses multilingual teams, and couples the plugin to a single locale forever.

### Option B — Everything in English, no i18n layer

The purist open-source default. Rejected: loses the multilingual UX that makes the plugin feel helpful, and the LLM would still need instructions somewhere to mirror the chat language.

### Option C — English artifacts, locale-aware runtime strings via a resolver

The chosen option. Splits the codebase along a clear axis: "seen by engineers during development" stays English; "seen by the user at runtime" is resolved via a tiny i18n module that falls back gracefully.

## Decision

We adopt **Option C**: a single runtime-string resolver in `core/i18n.py`, with pt-BR as the primary locale, English as the fallback, and a clear policy on which artifacts are localized and which are not.

### What stays in English (always)

- All Python source under `core/`, `skills/`, `hooks/`, `tests/`.
- All `SKILL.md` files (frontmatter `description:`, prose body, code blocks).
- All templates under `assets/vault-tree/**/_templates/`.
- All documentation under `docs/` (this file included).
- All Git commit messages, Conventional Commits types, branch names.
- The root `README.md` and `CHANGELOG.md`.

Rationale: these are the engineering surface. Keeping them English makes the project contributable by anyone fluent in English and avoids the "which language wins" bike-shed.

### What mirrors the user's chat language (runtime)

- Every line the skill speaks to the user via the LLM — questions in interviews, summaries, warnings, confirmations.
- The body of user-authored content inside scaffolded files (the LLM writes in the user's language; frontmatter stays in English).
- Status reports from the librarian.

Rationale: these are the UX. Matching the user's chosen language is the minimum bar for a tool that claims to be helpful.

### What is localized via `core/i18n.py`

A narrow set of strings emitted by the librarian that are not LLM-mediated — `_INDEX.md` section headings, empty-state CTAs, timestamps formatted as prose. These live in a `MESSAGES` dict keyed by locale, resolved via:

```python
t("pt-br", "index.heading", project="Acme")
```

Contract:

- Primary locale: `pt-br` (matches the 60+ strings already in the plugin when this ADR was written).
- Fallback locale: `en`.
- Missing key in target locale → fall back to `en`.
- Missing key in `en` too → return the key itself as a visible marker (not a silent empty string).

The locale for a given vault is stored in `.sdlc-kit/marker.json` under the `locale` field; defaults to `pt-br` when absent.

### Progressive English translation

English translations are added progressively — we do not block a feature on having its strings translated on day one. The fallback mechanism ensures an English-only vault still works (with a sprinkling of pt-BR keys visible until translated), and "translate remaining keys to English" becomes a steady stream of small, reviewable PRs rather than a blocker.

## Consequences

### Positive

- **The plugin is contributable in English.** Every file a contributor opens is in English. They can read, review, and refactor without context switching.
- **The UX stays warm in pt-BR.** Existing users see no regression in the runtime experience.
- **The locale axis is clear.** "Is this string emitted to the user at runtime, or is it part of the engineering surface?" is a question with a single answer.
- **The `README.md` and `docs/` are discoverable to an international audience.** The project can show up in English search results.

### Negative

- **Two sources of truth exist briefly.** While English keys are being added to `MESSAGES`, some strings exist only in pt-BR. We accept this as transitional and track progress in the CHANGELOG.
- **The LLM must know which language axis applies.** Every skill's `SKILL.md` explicitly says "mirror the user's chat language" for user-facing lines. Reviewers check that new skills carry this instruction.
- **Localized runtime strings are harder to grep.** A key like `index.panorama.heading` is less self-evident than an inline literal. We mitigate by keeping keys short, dotted, and hierarchical.

### Neutral

- Adding a third locale (e.g., `es` or `fr`) is mechanical — add a new top-level key to `MESSAGES` and progressively translate. The architecture does not need to change.
- Templates under `assets/vault-tree/**/_templates/` ship in English. When a user scaffolds a new file, the LLM translates the template prose into the user's chat language at edit time, not at copy time. This keeps templates maintainable centrally.

## Implementation plan

- [x] Create `core/i18n.py` with `MESSAGES`, `t()`, `available_locales()`, `list_keys()`.
- [x] Migrate the 60+ pt-BR strings from `sync.py` into `MESSAGES["pt-br"]`.
- [x] Add the `locale` field to `marker.json` (default `pt-br` when absent).
- [ ] Add English translations for `index.*` keys (first cohort — `_INDEX.md` headings).
- [ ] Update every `SKILL.md` to carry the "mirror the user's chat language" instruction (done in the canonical format migration).
- [ ] Expand `docs/CONTRIBUTING.md` with a short "adding a new message key" section.

## References

- [[CONTRIBUTING]]
- [[ARCHITECTURE]]
- [[ADR-0001-estrutura-canonica]]
- [[ADR-0002-skills-inventory]]
- [[ADR-0003-test-strategy-tdd-pbt]]
- `core/i18n.py` — the resolver.
- Root `~/.claude/CLAUDE.md` — establishes the "LLM mirrors the user's chat language" convention at the org level.
