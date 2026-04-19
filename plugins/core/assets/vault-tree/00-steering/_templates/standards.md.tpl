---
type: steering-standards
title: "Team Standards — {{PROJECT_NAME}}"
slug: "standards"
status: draft
phase: 00
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-steer
owner: "{{OWNER}}"
tags: [steering, standards, quality]
---

# Team Standards — {{PROJECT_NAME}}

> _(How the team works: commits, branches, PRs, review and Definition of Done.)_

## Conventional Commits

Mandatory format:

```
<type>(<optional scope>): <imperative description in English>

<optional body>

<optional footer: BREAKING CHANGE, refs>
```

**Accepted types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

## Branch flow

- **Main branch:** `main` — always deployable.
- **Feature branch:** `feat/<slug>` or `claude/feat/<slug>` (AI work).
- **Bugfix branch:** `fix/<slug>`.
- **Chore branch:** `chore/<slug>`.
- Never commit feature work directly to `main`.

## Pull Request flow

1. Create branch from updated `main`.
2. TDD: write tests before implementation.
3. Commit with Conventional Commits.
4. Push and open PR with filled template.
5. Green CI required before review.
6. Review follows checklist below.
7. Merge via squash (clean history).

## Code review checklist

- [ ] Design and architecture fit the use case.
- [ ] No Clean Architecture / DDD / SOLID violations.
- [ ] Tests cover edge cases (empty, null, boundary).
- [ ] Coverage ≥ 85% in modified package.
- [ ] No vulnerabilities (injection, authN/authZ, SSRF, secrets).
- [ ] LGPD compliance (PII minimized/masked).
- [ ] Error messages don't leak internal details.
- [ ] Conventional Commits respected.
- [ ] Documentation updated (if applicable).

## Definition of Done

A task is "done" only when:

- [ ] Code implemented and committed.
- [ ] Automated tests passing (unit + integration where applicable).
- [ ] Coverage within minimum defined.
- [ ] Code review approved.
- [ ] CI green (lint + tests + security scan).
- [ ] Documentation updated (README, ADR, spec).
- [ ] Merged to `main`.
- [ ] Monitored in production (if applicable).

## Code style

- **Language A:** <specific rules, ex: `gofmt`, `golangci-lint`>.
- **Language B:** <specific rules, ex: ESLint + Prettier>.
- **Naming:** <conventions>.
- **Comments:** explain _why_, not _what_.

## References

- [[product]] — product vision
- [[tech]] — technical principles
- [[CLAUDE]] — vault doctrine
