---
type: spec-tasks
title: "Tasks — {{TITLE}}"
slug: "{{SLUG}}"
status: draft
phase: 04
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-spec
owner: "{{OWNER}}"
tags: [spec, tasks]
feature: "{{SLUG}}"
---

# Tasks — {{TITLE}}

> _(Executable task list for the feature — every task is TDD-driven, bite-sized (2–5 min per step), and runs inside a dedicated git worktree branch named with Conventional Commits.)_

## How to read this file

### Status markers (Kiro convention)

| Marker      | Logical status    | Meaning                                                    |
|-------------|-------------------|------------------------------------------------------------|
| `- [ ]`     | `queued`          | Planned, not started.                                      |
| `- [-]`     | `in_progress`     | Actively being worked on. **Only ONE task at a time.**     |
| `- [x]`     | `completed`       | Delivered, merged, worktree cleaned up.                    |
| `- [~]`     | `needs_attention` | Blocked; awaiting human decision. Reason noted below line. |

Transitions are driven by `/sdlc-kit:task {start|complete|block|reopen}` — never edit markers by hand. Notes added under a `- [~]` line explain the blocker in one sentence.

### Invariants for every TASK

1. **TDD is mandatory.** Every task follows red → green → refactor:
   - Step 1: write the failing test.
   - Step 2: run the test and confirm it fails for the expected reason.
   - Step 3: write the minimum code to make it pass.
   - Step 4: run the test and confirm it passes.
   - Step 5: refactor only if the green bar stays green.
   - Step 6: commit using Conventional Commits.
2. **Bite-sized.** A task must fit in ≤ 2 hours of focused work and must be decomposed into 2–5 minute steps. If a step grows, split it.
3. **One worktree per task.** Work happens on an isolated `git worktree` branch; main stays clean.
4. **Conventional Commits for branch and commit.** Branch name **and** commit message both use CC syntax — `<type>(<scope>)/<slug>` for the branch, `<type>(<scope>): <subject>` for the commit.

### Conventional Commits — allowed branch types

| Type       | When to use                                          | Example branch               |
|------------|------------------------------------------------------|------------------------------|
| `feat`     | New user-facing capability.                          | `feat({{SLUG}})/login-form`  |
| `fix`      | Bug fix.                                             | `fix({{SLUG}})/null-guard`   |
| `refactor` | Restructure without changing behavior.               | `refactor({{SLUG}})/split-svc` |
| `test`     | Add or improve tests only.                           | `test({{SLUG}})/edge-cases`  |
| `docs`     | Documentation only.                                  | `docs({{SLUG}})/api-examples` |
| `chore`    | Tooling, deps, config — no production-code impact.   | `chore({{SLUG}})/bump-pg`    |
| `perf`     | Performance improvement.                             | `perf({{SLUG}})/cache-hit`   |
| `build`    | Build system / external deps.                        | `build({{SLUG}})/docker-base` |
| `ci`       | CI pipeline only.                                    | `ci({{SLUG}})/add-trivy`     |

Slug after the `/` is `kebab-case`, ≤ 40 chars, describes the task subject. Example: `feat({{SLUG}})/login-http-handler`.

### Git worktree workflow (per task)

Every task is executed inside an isolated worktree. The skeleton — adapt paths to your project's worktree directory (`.worktrees/` preferred, per `superpowers:using-git-worktrees`):

```bash
# 1. Create worktree + branch from up-to-date main
git fetch origin
git worktree add .worktrees/<branch-slug> -b <cc-branch-name> origin/main

# 2. Enter and set up the workspace (project-specific; npm install / go mod download / etc.)
cd .worktrees/<branch-slug>
<setup-command>

# 3. TDD loop — red/green/refactor, committing each pass with CC messages
#    Commit messages mirror the branch type, e.g.:
#      test({{SLUG}}): add failing test for <behavior>
#      feat({{SLUG}}): implement <behavior>
#      refactor({{SLUG}}): extract <helper>

# 4. Push and open PR
git push -u origin <cc-branch-name>
gh pr create --fill --base main

# 5. After PR is merged, clean up
cd ../..
git worktree remove .worktrees/<branch-slug>
git branch -d <cc-branch-name>
```

## Task template (copy this block when adding new tasks)

```
- [ ] **TASK-NNN** — <short imperative title>
  - **Branch:** `<cc-type>({{SLUG}})/<task-slug>`
  - **Worktree:** `.worktrees/<task-slug>`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-NNN]]
  - **Steps:**
    1. Write failing test `<path/to/test>` asserting `<behavior>`.
    2. Run `<test-command>` — expect failure with `<expected-error>`.
    3. Implement minimal change in `<path/to/file>` to satisfy the test.
    4. Run `<test-command>` — expect pass.
    5. Refactor (optional) — extract `<helper>` if it clarifies intent.
    6. Commit: `<cc-type>({{SLUG}}): <commit-subject>`.
    7. Push branch + open PR.
    8. After merge: `git worktree remove` and delete branch.
```

---

## Phase 1 — Setup

- [ ] **TASK-001** — Scaffold module `<path/in/code>` with entrypoint and empty public API.
  - **Branch:** `chore({{SLUG}})/scaffold-module`
  - **Worktree:** `.worktrees/scaffold-module`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-001]]
  - **Steps:**
    1. Write test `<module>_test.<ext>` asserting the module can be imported and exposes `<Fn>` as a callable stub.
    2. Run the test — expect `ModuleNotFound` / `ImportError` / equivalent.
    3. Create `<module>` file with a stub `<Fn>` that raises `NotImplementedError`.
    4. Run the test — expect pass (import + callable shape only).
    5. Commit: `chore({{SLUG}}): scaffold <module> with empty <Fn>`.
    6. Push + open PR + merge + cleanup worktree.

## Phase 2 — Domain logic (TDD)

- [ ] **TASK-010** — Implement `<Service.Create>` — happy path.
  - **Branch:** `feat({{SLUG}})/service-create-happy-path`
  - **Worktree:** `.worktrees/service-create-happy-path`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-002]]
  - **Steps:**
    1. Write failing test asserting `Create(validInput)` returns an entity with assigned ID and expected fields.
    2. Run test — expect fail (`NotImplementedError`).
    3. Implement the happy path inside `<Service.Create>` — no validation yet.
    4. Run test — expect pass.
    5. Commit: `feat({{SLUG}}): add <Service.Create> happy path`.
    6. Push + PR + merge + cleanup.

- [ ] **TASK-011** — Add input validation to `<Service.Create>` (one rule per test).
  - **Branch:** `feat({{SLUG}})/service-create-validation`
  - **Worktree:** `.worktrees/service-create-validation`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-003]]
  - **Steps:**
    1. Write failing test for rule A (e.g., empty name rejected).
    2. Run test — expect fail.
    3. Implement rule A.
    4. Run test — expect pass. Commit: `feat({{SLUG}}): reject empty <field>`.
    5. Repeat steps 1–4 for each additional rule (one commit per rule, keeps commits bite-sized).
    6. Push + PR + merge + cleanup.

## Phase 3 — Transport

- [ ] **TASK-020** — HTTP handler `POST /<resource>` — happy path.
  - **Branch:** `feat({{SLUG}})/http-create-handler`
  - **Worktree:** `.worktrees/http-create-handler`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-004]]
  - **Steps:**
    1. Write failing integration test posting a valid payload and asserting `201 Created` + response body.
    2. Run test — expect fail (route not registered).
    3. Register handler, wire to `<Service.Create>`, serialize the response.
    4. Run test — expect pass.
    5. Commit: `feat({{SLUG}}): add POST /<resource> handler`.
    6. Push + PR + merge + cleanup.

- [ ] **TASK-021** — HTTP handler — error mapping (one status per test).
  - **Branch:** `feat({{SLUG}})/http-create-errors`
  - **Worktree:** `.worktrees/http-create-errors`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-004]]
  - **Steps:**
    1. Write failing test for validation error → `400`.
    2. Run → fail → implement mapping → run → pass. Commit.
    3. Repeat for conflict → `409`, unauthorized → `401`, etc.
    4. Push + PR + merge + cleanup.

## Phase 4 — Observability

- [ ] **TASK-030** — Structured logs at service boundaries.
  - **Branch:** `feat({{SLUG}})/structured-logs`
  - **Worktree:** `.worktrees/structured-logs`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-005]]
  - **Steps:**
    1. Write failing test asserting a log line is emitted on `<Service.Create>` with `entity_id` and `correlation_id`.
    2. Run → fail → add structured log → run → pass.
    3. Commit: `feat({{SLUG}}): emit structured logs in <Service.Create>`.
    4. Push + PR + merge + cleanup.

- [ ] **TASK-031** — Counter + latency histogram metrics.
  - **Branch:** `feat({{SLUG}})/metrics-create`
  - **Worktree:** `.worktrees/metrics-create`
  - **Requirements satisfied:** [[{{SLUG}}-requirements#REQ-005]]
  - **Steps:**
    1. Write failing test asserting the metric is registered and incremented on success.
    2. Run → fail → instrument → run → pass.
    3. Commit: `feat({{SLUG}}): add counter + latency metrics for create`.
    4. Push + PR + merge + cleanup.

## Phase 5 — Deploy

- [ ] **TASK-040** — Run migration in staging (guarded rollout).
  - **Branch:** `chore({{SLUG}})/migrate-staging`
  - **Worktree:** `.worktrees/migrate-staging`
  - **Steps:**
    1. Dry-run the migration locally against a staging snapshot.
    2. Apply the migration in staging using the standard tooling.
    3. Verify schema via health check; if any verification fails, mark this task `- [~]` with the failure reason.
    4. Commit a CHANGELOG entry: `chore({{SLUG}}): migrate <table> in staging`.
    5. Push + PR + merge + cleanup.

- [ ] **TASK-041** — Canary deploy (10% traffic).
  - **Branch:** `chore({{SLUG}})/canary-10pct`
  - **Worktree:** `.worktrees/canary-10pct`
  - **Steps:**
    1. Ship image with the new code behind a 10% canary.
    2. Watch error rate + p95 latency for 30 min.
    3. If SLOs hold, advance the task; otherwise roll back and mark `- [~]` with the metric deviation.
    4. Commit the rollout note.
    5. Push + PR + merge + cleanup.

- [ ] **TASK-042** — Promote to 100% after 24h without incidents.
  - **Branch:** `chore({{SLUG}})/promote-100pct`
  - **Worktree:** `.worktrees/promote-100pct`
  - **Steps:**
    1. Confirm the canary has run 24h with no SLO regressions.
    2. Flip the traffic split to 100%.
    3. Keep the previous revision warm for 24h in case of fast rollback.
    4. Commit the rollout note.
    5. Push + PR + merge + cleanup.

## Summary

- **Total tasks:** <N>
- **Critical path:** TASK-001 → TASK-010 → TASK-020 → TASK-041
- **Parallelizable tracks:** observability (TASK-030..031) after TASK-010; deploy (TASK-040..042) after TASK-021.

## References

- **Requirements:** [[{{SLUG}}-requirements]]
- **Design:** [[{{SLUG}}-design]]
- [[_INDEX]] — global index
