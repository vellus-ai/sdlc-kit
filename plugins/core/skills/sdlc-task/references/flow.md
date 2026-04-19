# sdlc-kit:task — full flow

## Where tasks fit

```
04-specs/<feature>/
  ├─ requirements.md   (WHAT — EARS)
  ├─ design.md         (HOW — architecture, data, flows)
  └─ tasks.md          (WHEN/BY WHOM — TDD-driven, bite-sized, CC-branched)
                        └─ TASK-NNN lines carry the Kiro marker this skill flips
```

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Tasks file exists** at `<vault>/04-specs/<feature>/tasks.md`. If missing, point at `/sdlc-kit:spec`.

## Flow

### Zero-arg: `/sdlc-kit:task`

1. Ask which feature (or infer from recent activity).
2. Run `task.py --action list --feature <slug>` and summarize:
   - `TASK-001  queued       Scaffold module …`
   - `TASK-010  in_progress  Implement Service.Create happy path`
   - `TASK-020  needs_attention  HTTP handler — blocked: waiting on infra`
3. Suggest next action.

### `start`: `/sdlc-kit:task start <feature> <TASK-NNN>`

1. Run `task.py --action list --feature <slug>` to confirm nothing else is `[-]`.
2. **Set up the worktree before flipping the marker.** Invoke `superpowers:using-git-worktrees` to create `.worktrees/<task-slug>` from the CC branch name.
3. Run `task.py --action start --feature <slug> --id <TASK-NNN>`.
4. Walk the user through TDD steps (each 2–5 min; split if grows).
5. Invoke `/sdlc-kit:sync`.

If the script refuses (another task is `[-]`):
- Show the offending task id.
- Offer to `complete`, `block`, or `reopen` first.
- Never silently pass `--allow-multi-active`.

### `complete`: `/sdlc-kit:task complete <feature> <TASK-NNN>`

1. Verify PR merged + worktree can be cleaned.
2. Walk the cleanup: `git worktree remove .worktrees/<task-slug>` + `git branch -d <cc-branch-name>`.
3. Run `task.py --action complete --feature <slug> --id <TASK-NNN>`.
4. Invoke `/sdlc-kit:sync`.

### `block`: `/sdlc-kit:task block <feature> <TASK-NNN> "<reason>"`

1. Ask for the one-sentence reason if not provided.
2. Run `task.py --action block --feature <slug> --id <TASK-NNN> --note "<reason>"`.
3. Invoke `/sdlc-kit:sync`.
4. Offer to capture in a more durable place if needs follow-up.

### `reopen`: `/sdlc-kit:task reopen <feature> <TASK-NNN>`

1. Run `task.py --action reopen --feature <slug> --id <TASK-NNN>`.
2. If the task was `[~]`, the blocker note is removed automatically — confirm blocker is resolved.
3. Invoke `/sdlc-kit:sync`.

## The git worktree workflow (per task)

User runs themselves; the skill coaches.

```bash
# 1. From repo root, pull latest main.
git fetch origin && git checkout main && git pull --ff-only

# 2. Create worktree + CC branch (branch name on TASK line).
git worktree add .worktrees/<task-slug> -b <cc-type>(<feature>)/<task-slug> origin/main
cd .worktrees/<task-slug>

# 3. Project setup (npm install / go mod download / pip install / cargo build).

# 4. Execute TDD steps from TASK-NNN block:
#      test(<feature>): add failing test for <behavior>
#      feat(<feature>): implement <behavior>
#      refactor(<feature>): extract <helper>

# 5. Push and open PR targeting main.
git push -u origin <cc-type>(<feature>)/<task-slug>
gh pr create --fill --base main

# 6. After merge, clean up.
cd ../..
git worktree remove .worktrees/<task-slug>
git branch -d <cc-type>(<feature>)/<task-slug>
```

Worktree directory selection (`.worktrees/` vs `~/.config/…`) follows
`superpowers:using-git-worktrees` — verify directory is `.gitignore`d before
project-local worktrees.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "feature": "login-google",
  "tasks_path": "04-specs/login-google/tasks.md",
  "errors": [],
  "tasks": [
    {"id": "TASK-001", "line": 63, "marker": "[x]", "status": "completed",
     "title": "Scaffold module auth/login",
     "has_blocker_note": false, "blocker_note": ""},
    {"id": "TASK-010", "line": 70, "marker": "[-]", "status": "in_progress",
     "title": "Implement Service.Create happy path",
     "has_blocker_note": false, "blocker_note": ""}
  ],
  "count": 2
}

// --action start | complete | block | reopen
{
  "status": "ok", "action": "start",
  "vault_root": "/abs/path/.sdlc",
  "feature": "login-google",
  "tasks_path": "04-specs/login-google/tasks.md",
  "task_id": "TASK-010",
  "previous_marker": "[ ]", "new_marker": "[-]",
  "previous_status": "queued", "new_status": "in_progress",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug or id, tasks.md missing, task id not found, missing `--note` on block, single-`[-]` invariant violated) · `2` fatal.

## Guardrails

**Never:**
- Create a standalone `task` document.
- Rewrite task text, IDs, step bodies, requirement links, indentation, or phase headings — only the 3-char marker and adjacent blocker note.
- Flip a marker by hand — always go through `task.py`.
- Bypass single-`[-]` silently; users must opt in via `--allow-multi-active`.
- Generate a task that violates TDD / bite-sized / CC-branch / worktree-per-task — stop and ask for regeneration via `/sdlc-kit:spec`.
- Touch `CLAUDE.md`, `_INDEX.md`, or `_MOC.md`.

**Always:**
- Mirror user's chat language.
- Run `--action list` before any state change.
- Set up worktree **before** flipping `[ ]` → `[-]`.
- Require `--note` on `block`.
- Invoke `/sdlc-kit:sync` after any flip.
- If user is stuck > 2× on the same TDD step, offer to `block` and capture the reason.

## Examples

**Starting the first task:**
```
User: /sdlc-kit:task start login-google TASK-001
AI:   [list] no task is [-], proceeding.
AI:   "Setting up worktree first — branch `chore(login-google)/scaffold-module`."
AI:   [superpowers:using-git-worktrees → .worktrees/scaffold-module, baseline tests pass]
AI:   [task.py --action start --id TASK-001][/sdlc-kit:sync]
AI:   "TASK-001 is `[-] in_progress`. Step 1: write a failing test that imports `auth/login` and asserts `Create` stub is callable. Target language/test framework?"
```

**Blocking while waiting on infra:**
```
User: bloqueia TASK-022 — sem permissão no banco de staging
AI:   [task.py --action block --id TASK-022 --note "no DB permission on staging — INFRA-412"]
AI:   [/sdlc-kit:sync]
AI:   "TASK-022 marcada como `[~] needs_attention`. Quer registrar como risk no milestone?"
```

**Refusal under single-[-]:**
```
User: /sdlc-kit:task start login-google TASK-021
AI:   [list] TASK-010 is already `[-]`.
AI:   "Can't start TASK-021 — TASK-010 (`Service.Create happy path`) is in progress.
       Want to `complete`, `block`, or reopen first? If you really want both running parallel,
       I can pass `--allow-multi-active` — say so explicitly."
```

**Completing:**
```
User: /sdlc-kit:task complete login-google TASK-010
AI:   "Confirm: PR merged, worktree removable, tests green on main?"
User: sim
AI:   [guides: git worktree remove + git branch -d]
AI:   [task.py --action complete --id TASK-010][/sdlc-kit:sync]
AI:   "TASK-010 `[x] completed`. Next queued is TASK-011 — start it?"
```

## See also

- `scripts/task.py` — marker-flip helper.
- `assets/vault-tree/04-specs/_templates/tasks.md.tpl`.
- `/sdlc-kit:spec`, `/sdlc-kit:epic`, `/sdlc-kit:milestone`.
- `superpowers:using-git-worktrees`, `/sdlc-kit:sync`.
