---
name: sdlc-task
description: |
  Use when the user wants to list, start, complete, block, or reopen a
  TASK-NNN inside a feature's `04-specs/<slug>/tasks.md` — the executable
  task list authored by `/sdlc-kit:spec`. English triggers:
  `/sdlc-kit:task`, `/sdlc-kit:task list <feature>`,
  `/sdlc-kit:task start <feature> <TASK-NNN>`,
  `/sdlc-kit:task complete <feature> <TASK-NNN>`,
  `/sdlc-kit:task block <feature> <TASK-NNN> "<reason>"`,
  `/sdlc-kit:task reopen <feature> <TASK-NNN>`,
  "start TASK-010 for login", "complete TASK-001 on checkout",
  "block TASK-022 — waiting on infra", "reopen TASK-015". pt-BR triggers:
  "começar a TASK-010 do login", "finalizar a TASK-001 do checkout",
  "bloquear a TASK-022 — esperando infra", "reabrir a TASK-015".
  Driven by a **Senior Engineer** persona — enforces TDD, bite-sized steps
  (2–5 min), one worktree per task, Conventional Commits for branch and
  commit, and the single-`[-]` invariant per feature. This skill does not
  create a standalone `task` document; the spec-tasks file is the single
  source of truth. The script flips Kiro markers only (`[ ]` queued →
  `[-]` in_progress → `[x]` completed; `[~]` needs_attention with a note).
  Every task is executed TDD-first, bite-sized, inside a dedicated
  `git worktree` branch named with Conventional Commits
  (`feat(<feature>)/<task-slug>`, `fix(<feature>)/...`, `refactor(...)/...`,
  etc.). Only one task per feature may be in `[-]` at a time (the script
  refuses unless `--allow-multi-active` is passed). Always invokes
  `/sdlc-kit:sync` after any marker change. Do not invoke for creating the
  task list (`/sdlc-kit:spec`), for grouping features (`/sdlc-kit:epic`),
  or for delivery windows (`/sdlc-kit:milestone`).
---

# sdlc-kit:task

Operator for the Kiro-style status markers inside a feature's `04-specs/<slug>/tasks.md`. Authoring the task list is `/sdlc-kit:spec`'s job; **executing** it is this skill's job.

---

## Where tasks fit

```
04-specs/<feature>/
  ├─ requirements.md   (WHAT — EARS)
  ├─ design.md         (HOW — architecture, data, flows)
  └─ tasks.md          (WHEN/BY WHOM — TDD-driven, bite-sized, CC-branched)
                        └─ TASK-NNN lines carry the Kiro marker this skill flips
```

The tasks.md file is authored once by `/sdlc-kit:spec` (after design is approved). Each `TASK-NNN` line has:

- a Kiro marker (`[ ]` / `[-]` / `[x]` / `[~]`);
- a bold TASK id and short imperative title;
- a Conventional Commits branch name and matching worktree path;
- a requirements back-reference;
- numbered bite-sized TDD steps (red → green → refactor → commit → PR).

This skill does not touch text, steps, IDs, or links — only the marker and (for blockers) an adjacent note line.

---

## Kiro marker conventions

| Marker  | Logical status    | Meaning                                                    | Notes |
|---------|-------------------|------------------------------------------------------------|-------|
| `- [ ]` | `queued`          | Planned, not started.                                      | Default state at scaffold. |
| `- [-]` | `in_progress`     | Actively worked on. **Exactly one per feature** at a time. | Enforced by the script. |
| `- [x]` | `completed`       | Delivered — PR merged, worktree cleaned, tests green.      | Terminal (until `reopen`). |
| `- [~]` | `needs_attention` | Blocked; the blocker is written on the next line.          | Requires `--note`. |

The script is the only sanctioned way to flip these; the user should not edit markers by hand, because:

- `start` enforces the single-`[-]` invariant;
- `block` manages the blocker note (insert/replace/clean up);
- every write refreshes the `updated:` frontmatter.

---

## Non-negotiable execution rules

These apply to **every** TASK-NNN the user starts. The LLM must honor them, and `/sdlc-kit:spec` must generate task lists that already conform.

1. **TDD is mandatory.** Red → green → refactor → commit. No code without a failing test. Applies to every step that changes production code.
2. **Bite-sized steps.** Each numbered step fits in 2–5 minutes. If a step grows, split the task or add sub-steps. A task that cannot be described in ≤ 8 steps is too big — split it.
3. **One worktree per task.** Work happens on an isolated `git worktree` branch; `main` stays clean. Follow `superpowers:using-git-worktrees` for directory selection and safety verification.
4. **Conventional Commits for branch and commit.** The branch name uses CC syntax: `<type>(<feature>)/<task-slug>` (kebab-case slug, ≤ 40 chars). The commit messages use matching CC types (`feat(<feature>): …`, `test(<feature>): …`, `refactor(<feature>): …`). See the allowed-types table in `tasks.md.tpl`.
5. **Single in-progress per feature.** Only one TASK may be `[-]` at a time in a given tasks.md. The script refuses to start another unless `--allow-multi-active` is passed (reserved for deliberate parallel tracks the user understands and accepts).

Violating any of these is a strong signal to pause and re-plan — not to push through.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:task …` or invokes it from the zero-arg prompt.
- The user says "start TASK-010 for login", "complete TASK-001 on checkout", "block TASK-022 — waiting on infra", "reopen TASK-015 from payments", or equivalent phrasing in any language.
- After `/sdlc-kit:spec new <feature>` has produced the trio and the engineer is ready to begin the first task.

**Do not** invoke when:

- The user wants to generate/regenerate the task list → use `/sdlc-kit:spec`.
- The user wants to group features → use `/sdlc-kit:epic`.
- The user wants a delivery window → use `/sdlc-kit:milestone`.
- The referenced feature has no `tasks.md` yet → run `/sdlc-kit:spec new <feature>` first.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Tasks file exists** at `<vault>/04-specs/<feature>/tasks.md`. If missing, point the user at `/sdlc-kit:spec`.

---

## Flow

### Zero-arg: `/sdlc-kit:task`

1. Ask the user which feature they want to work on (or infer from recent activity).
2. Run `task.py --action list --feature <slug>` and summarize:
   - `TASK-001  queued       Scaffold module …`
   - `TASK-010  in_progress  Implement Service.Create happy path`
   - `TASK-020  needs_attention  HTTP handler — blocked: waiting on infra`
3. Suggest next action:
   - If any task is `in_progress` → "Still working on `<id>`? Ready to `complete`?"
   - If any task is `needs_attention` → "Want to unblock `<id>` (reopen) or still stuck?"
   - Else → "Next queued is `<id>`. Start it?"

### `start`: `/sdlc-kit:task start <feature> <TASK-NNN>`

1. Run `task.py --action list --feature <slug>` to confirm nothing else is `[-]` in this feature.
2. **Set up the worktree before flipping the marker.** Invoke `superpowers:using-git-worktrees` to create `.worktrees/<task-slug>` from the CC branch name declared on the TASK line.
3. Run `task.py --action start --feature <slug> --id <TASK-NNN>`.
4. Walk the user through the TDD steps in order. Keep each step in the 2–5 minute range; split if it grows.
5. Invoke `/sdlc-kit:sync`.

If the script refuses because another task is already `[-]`:

- Show the offending task id.
- Offer to `complete`, `block`, or `reopen` that one first.
- Never silently pass `--allow-multi-active` without explicit user consent.

### `complete`: `/sdlc-kit:task complete <feature> <TASK-NNN>`

1. Verify the PR for the task branch is merged and the worktree can be cleaned.
2. Walk the cleanup: `git worktree remove .worktrees/<task-slug>` + `git branch -d <cc-branch-name>`.
3. Run `task.py --action complete --feature <slug> --id <TASK-NNN>`.
4. Invoke `/sdlc-kit:sync`.

### `block`: `/sdlc-kit:task block <feature> <TASK-NNN> "<reason>"`

1. Ask for the one-sentence blocker reason if the user didn't provide one.
2. Run `task.py --action block --feature <slug> --id <TASK-NNN> --note "<reason>"`.
3. Invoke `/sdlc-kit:sync`.
4. Offer to capture the blocker in a more durable place if it needs follow-up (new ADR, epic note, etc.).

### `reopen`: `/sdlc-kit:task reopen <feature> <TASK-NNN>`

1. Run `task.py --action reopen --feature <slug> --id <TASK-NNN>`.
2. If the task was `[~]`, the blocker note is removed automatically — confirm with the user that the blocker is truly resolved.
3. Invoke `/sdlc-kit:sync`.

---

## The git worktree workflow (per task)

The user runs this themselves; the skill coaches it and does not fabricate git commands.

```bash
# 1. From the repo root, pull latest main.
git fetch origin && git checkout main && git pull --ff-only

# 2. Create worktree + CC branch (branch name declared on the TASK line).
git worktree add .worktrees/<task-slug> -b <cc-type>(<feature>)/<task-slug> origin/main
cd .worktrees/<task-slug>

# 3. Run project-specific setup (npm install / go mod download / pip install / cargo build).

# 4. Execute the TDD steps from the TASK-NNN block:
#      test(<feature>): add failing test for <behavior>
#      feat(<feature>): implement <behavior>
#      refactor(<feature>): extract <helper>
#    One commit per step, CC messages mandatory.

# 5. Push and open a PR targeting main.
git push -u origin <cc-type>(<feature>)/<task-slug>
gh pr create --fill --base main

# 6. After merge, clean up.
cd ../..
git worktree remove .worktrees/<task-slug>
git branch -d <cc-type>(<feature>)/<task-slug>
```

Worktree directory selection (`.worktrees/` vs. `~/.config/…`) follows `superpowers:using-git-worktrees` — verify the directory is `.gitignore`d before creating project-local worktrees.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "feature": "login-google",
  "tasks_path": "04-specs/login-google/tasks.md",
  "errors": [],
  "tasks": [
    {
      "id": "TASK-001",
      "line": 63,
      "marker": "[x]",
      "status": "completed",
      "title": "Scaffold module auth/login",
      "has_blocker_note": false,
      "blocker_note": ""
    },
    {
      "id": "TASK-010",
      "line": 70,
      "marker": "[-]",
      "status": "in_progress",
      "title": "Implement Service.Create happy path",
      "has_blocker_note": false,
      "blocker_note": ""
    }
  ],
  "count": 2
}

// --action start | complete | block | reopen
{
  "status": "ok",
  "action": "start",
  "vault_root": "/abs/path/.sdlc",
  "feature": "login-google",
  "tasks_path": "04-specs/login-google/tasks.md",
  "task_id": "TASK-010",
  "previous_marker": "[ ]",
  "new_marker": "[-]",
  "previous_status": "queued",
  "new_status": "in_progress",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug or id, tasks.md missing, task id not found, missing `--note` on block, single-`[-]` invariant violated) · `2` fatal (permission denied, IO).

---

## Guardrails

**Never:**
- Create a standalone `task` document — the spec-tasks file is the single source of truth.
- Rewrite task text, IDs, step bodies, requirement links, indentation, or phase headings — only the 3-char marker and the adjacent blocker note.
- Flip a marker by hand — always go through `task.py`.
- Bypass the single-`[-]` invariant silently; if the user wants parallel tracks, they must opt in via `--allow-multi-active`.
- Generate a task that violates TDD, bite-sized, CC-branch, or worktree-per-task rules — if a TASK line does, stop and ask for a regeneration via `/sdlc-kit:spec`.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md`.

**Always:**
- Mirror the user's active conversation language.
- Run `--action list` before any state change to show current status.
- Set up the worktree **before** flipping `[ ]` → `[-]`.
- Require a `--note` on `block` — no silent blockers.
- Invoke `/sdlc-kit:sync` after any flip.
- If the user is stuck more than twice on the same TDD step, offer to `block` the task and capture the reason.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Starting the first task of a feature:**
```
User: /sdlc-kit:task start login-google TASK-001
AI:   [list --feature login-google] → no task is [-], proceeding.
AI:   "Setting up worktree first — branch `chore(login-google)/scaffold-module`."
AI:   [superpowers:using-git-worktrees → .worktrees/scaffold-module, baseline tests pass]
AI:   [task.py --action start --feature login-google --id TASK-001]
AI:   [/sdlc-kit:sync]
AI:   "TASK-001 is now `[-] in_progress`. Step 1: write a failing test that
       imports `auth/login` and asserts the `Create` stub is callable.
       What's the target language/test framework for this repo?"
```

**Blocking while waiting on infra:**
```
User: bloqueia TASK-022 — estamos sem permissão no banco de staging
AI:   [task.py --action block --feature login-google --id TASK-022
         --note "no DB permission on staging — opened ticket INFRA-412"]
AI:   [/sdlc-kit:sync]
AI:   "TASK-022 marcada como `[~] needs_attention`. Quer que eu registre
       isso como um risk ativo no milestone associado?"
```

**Refusal under the single-[-] invariant:**
```
User: /sdlc-kit:task start login-google TASK-021
AI:   [list] → TASK-010 is already `[-]`.
AI:   "Can't start TASK-021 yet — TASK-010 (`Service.Create happy path`) is
       still in progress. Want to `complete` it, `block` it, or reopen it
       first? If you really want both running in parallel, I can pass
       `--allow-multi-active`, but say so explicitly."
```

**Completing a task:**
```
User: /sdlc-kit:task complete login-google TASK-010
AI:   "Before flipping, confirm: PR merged, worktree removable, tests green
       on main?"
User: sim
AI:   [guides: git worktree remove + git branch -d]
AI:   [task.py --action complete --feature login-google --id TASK-010]
AI:   [/sdlc-kit:sync]
AI:   "TASK-010 `[x] completed`. Next queued is TASK-011 — want to start it?"
```

**Zero-arg overview:**
```
User: /sdlc-kit:task
AI:   "Which feature? Recent: login-google, billing-rewrite."
User: login-google
AI:   [list --feature login-google]
AI:   TASK-001  [x] completed       Scaffold module auth/login
      TASK-010  [-] in_progress     Implement Service.Create happy path
      TASK-020  [~] needs_attention HTTP handler — blocked: waiting on infra
      TASK-011  [ ] queued          Add input validation
      …
AI:   "Still on TASK-010. Keep going, or check in on the blocker for TASK-020?"
```

---

## See also

- `scripts/task.py` — marker-flip helper.
- `assets/vault-tree/04-specs/_templates/tasks.md.tpl` — canonical task-list template, authored by `/sdlc-kit:spec`.
- `/sdlc-kit:spec` — scaffolds the requirements/design/tasks trio; owns the content of tasks.md.
- `/sdlc-kit:epic` — large deliverable grouping stories that become spec trios.
- `/sdlc-kit:milestone` — delivery window grouping epics.
- `superpowers:using-git-worktrees` — directory selection and safety verification for the per-task worktree.
- `/sdlc-kit:sync` — always invoked after marker flips.
