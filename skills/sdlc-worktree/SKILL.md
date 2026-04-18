---
name: sdlc-worktree
description: |
  Use when the user asks to create, register, close, merge, or abandon a git
  worktree or a feature branch — or when they invoke `/sdlc-kit:worktree`.
  Mirror triggers such as "create a worktree", "register a branch", "open a
  feature branch", "mark worktree as merged", "close this worktree",
  "abandon the branch", "criar worktree", "registrar branch", "abrir branch
  de feature", "marcar worktree como mergeado", "fechar worktree", "abandonar
  worktree". Operates under `05-development/` with two kinds, both
  collections: `worktree` (physical git worktree directory — lifecycle
  `active → merged | abandoned`) and `branch` (git branch record — no formal
  status enum, tracks `ci_status`/`pr` instead). The skill scaffolds the file
  and, for worktrees, records the status change. The **Senior Software
  Engineer** and the **Release Engineer / Branch Manager** drive the
  closure interview together; both must agree before a worktree can be
  transitioned to `merged`.
---

# sdlc-kit:worktree

Tracks the **developer-facing side of SDLC execution** under
`05-development/`: the git worktrees that materialize in the filesystem and
the branches that record the commit trail. The skill is co-authored by two
lenses working in tandem:

- **Senior Software Engineer / Developer-ergonomics lens** — owns day-to-day
  isolation: one worktree per feature, clean base, fast iteration, agent
  attached to the right directory, no stale state polluting `main`.
- **Release Engineer / Branch Manager lens** — owns merge-state hygiene: PR
  opened, CI green, reviewers signed off, squash merge, local branch and
  worktree directory removed, retro/post-mortem linked. Source of truth for
  "is this safely merged?".

A worktree becomes `merged` only when both lenses agree. `abandoned` is the
explicit exit for work that is never merged (spike that failed, direction
change, idea parked). Never silently delete a worktree record — the git
worktree can be removed from disk, but the `.md` record stays as history.

## Kinds, paths and templates

| Kind       | Type slug (frontmatter) | Cardinality           | Path                                   | Template                                    |
|------------|-------------------------|-----------------------|----------------------------------------|---------------------------------------------|
| `worktree` | `worktree`              | Collection (per slug) | `05-development/worktrees/<slug>.md`   | `_templates/worktree.md.tpl`                |
| `branch`   | `branch`                | Collection (per slug) | `05-development/branches/<slug>.md`    | `_templates/branch.md.tpl`                  |

Both kinds require `--slug` and `--title` on `scaffold`.

## Lifecycle

### `worktree`
```
active  →  merged
active  →  abandoned
```
- `active` — scaffolded state. The git worktree directory may or may not
  exist yet on disk, but the record is open and tracks ongoing work.
- `merged` — PR merged, branch deleted, worktree directory removed. Terminal.
- `abandoned` — work discarded before merge; worktree directory removed,
  branch deleted or left stale. Terminal. The body should explain *why* —
  future readers need to understand the decision.

### `branch`
Branches have **no formal status enum**. A branch record tracks:
- `branch_type` (`feat` / `fix` / `chore` / `refactor` / `docs` / `test`)
- `base` (usually `main`)
- `pr` (PR number/URL once opened)
- `ci_status` (`passing` / `running` / `failed` / `pending` — edit in the
  body directly; no `transition` action)

Because there is no enum, the `transition` action is **refused for kind
`branch`**. The script returns exit code 1 with a clear error. Update the
body (CI status, commits table, PR number) via Edit/Write instead.

## When to invoke

- User says *"create a worktree for feature X"*, *"criar worktree para feat-
  login"* → scaffold `worktree`; interview them on branch name, base SHA,
  local path; point them at the reference `git worktree add` command in the
  template.
- User says *"register this branch"*, *"registrar o branch feat-api"* →
  scaffold `branch`; capture `branch_type`, PR link (if already open),
  linked tasks.
- User reports *"PR merged"*, *"terminei a feature"*, *"marcar como
  mergeado"* → validate the pre-merge checklist, then
  `transition --kind worktree --to merged`.
- User reports *"vou abandonar esse worktree"*, *"esse spike não deu em
  nada"* → `transition --kind worktree --to abandoned`; ensure the body
  records the reason.
- User wants a roll-up → `list` or `list --kind worktree`.

## When **not** to invoke

- Implementation plan / task tracking → that's `/sdlc-kit:task`.
- Feature spec, design notes → that's `/sdlc-kit:spec`.
- Post-merge retrospective, incident review → that's `/sdlc-kit:retro` or
  `/sdlc-kit:incident`.
- CI pipeline configuration → not an SDLC Kit artifact (lives in the repo,
  not the vault).

## Flow

### 1. Pre-flight
- Run `list` first. **Never scaffold on top of an existing record without
  `--force`** — the script refuses and so must the skill.
- Read the vault's `CLAUDE.md` if it exists — it may pin branch naming
  conventions, base branch policies, or merge strategy.

### 2. Scaffold
Run `scripts/worktree.py --action scaffold` with:
- `--kind {worktree|branch}`
- `--slug <slug>` (required; must match `[a-z0-9][a-z0-9-]*`)
- `--title "<human title>"` (required)
- `--owner <handle>` (optional; falls back to marker.json owner)

The script:
- validates the slug
- refuses to overwrite unless `--force` is passed
- substitutes `{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`,
  `{{PROJECT_NAME}}` in the template
- emits a JSON report with the final path

### 3. Interview (per kind)
Walk the user through the template body. Fill via Edit/Write in the user's
chat language; keep frontmatter keys/values in English.

| Kind       | Must-fill sections                                                                             |
|------------|------------------------------------------------------------------------------------------------|
| `worktree` | Branch name, base SHA, local path, linked feature/task, agent_active checkbox, history entry  |
| `branch`   | Branch name, type, base, PR link (if open), linked task(s), CI status, main commits table     |

Every missing field must either be filled or explicitly marked `— N/A —`
with a 1-line justification.

### 4. Cross-link
- A `worktree` record's *References* section must wikilink its matching
  `branch` record (`[[<branch-slug>]]`) and vice-versa if both exist.
- Both should wikilink the feature design (`[[<feature>-design]]`) and the
  relevant task IDs (`[[<feature>-tasks#TASK-NNN]]`).

### 5. Transition (worktree only)
When the PR is merged and the worktree is cleaned up:
```
scripts/worktree.py --action transition --kind worktree --slug <slug> --to merged
```
When the work is discarded:
```
scripts/worktree.py --action transition --kind worktree --slug <slug> --to abandoned
```
The action is idempotent — re-running with the same target is a no-op.

## Pre-merge checklist (hard gate for `--to merged`)

Block `transition --to merged` unless **all** of the following are true —
this is a duo sign-off: the Senior SWE confirms the first three, the Release
Engineer confirms the last three:

- [ ] CI is green on the final commit of the branch (SWE).
- [ ] PR has been approved and **actually merged** into the base branch (Release).
- [ ] Local feature branch has been deleted (`git branch -d <branch>`) (SWE).
- [ ] Worktree directory has been removed from the filesystem
      (`git worktree remove <path>`) (SWE).
- [ ] `/sdlc-kit:sync` has been run so `_INDEX.md` reflects the new state
      (Release).
- [ ] Any follow-up issues (tech debt spotted in review, missing tests) have
      a corresponding task or TRD entry scaffolded (Release).

If any box is unchecked: **do not transition**. Keep the worktree `active`
and list the missing items for the user.

## Output contract

All actions emit a single JSON object on stdout. Common fields: `status`,
`action`, `vault_root`, `errors`.

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`,
  `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`,
  `new_status` (equal on idempotent re-runs).

Exit codes: `0` ok/dry-run, `1` user error (invalid kind/slug/status,
missing required arg, transition attempted on `branch`), `2` fatal
(template missing, filesystem failure).

## Guardrails

**Never:**
- Delete a worktree or branch `.md` record. If the work is discarded,
  transition the worktree to `abandoned` and record why in the body. If a
  branch record is truly obsolete, leave it — it is part of history.
- Rename a slug. Backlinks in feature designs, task notes, and PR reviews
  would break. If the identity must change, scaffold a new record and note
  the replacement in the body of the old one.
- Call `transition` on kind `branch` — the script refuses, and the skill
  must not try. Edit the body (CI status, commits) directly instead.
- Promote a worktree to `merged` without the full pre-merge checklist
  passing and both lenses (Senior SWE + Release Engineer) signing off.
- Scaffold over an existing record without `--force` and an explicit
  reason from the user.

**Always:**
- Prefer `abandoned` over silent deletion for worktrees that won't merge —
  the `.md` record preserves decision history.
- Keep the `updated` field honest — the `transition` action refreshes it
  automatically.
- Run `/sdlc-kit:sync` after any scaffold or transition so `_INDEX.md`
  reflects reality.
- Mirror the user's chat language in the body; keep frontmatter and
  template scaffolding in English.

## Examples

### Open a new worktree for a feature
```
scripts/worktree.py --action scaffold --kind worktree \
  --slug feat-login --title "Login feature" --owner milton
```
Then interview the user to fill branch name (e.g. `feat/login`), base
commit SHA, local path (`../project-feat-login`), linked feature/task.

### Register the matching branch record
```
scripts/worktree.py --action scaffold --kind branch \
  --slug feat-login --title "feat/login"
```
Fill `branch_type: feat`, base, CI status in the body. Cross-link the
worktree record.

### List every open worktree
```
scripts/worktree.py --action list --kind worktree
```

### Mark a worktree as merged (after the pre-merge checklist passes)
```
scripts/worktree.py --action transition --kind worktree \
  --slug feat-login --to merged
```
Then run `/sdlc-kit:sync` to refresh `_INDEX.md`.

### Smell: transition requested on a branch
If the user asks to "mark branch `feat-login` as merged" via `transition
--kind branch`, refuse. Explain that branches carry `ci_status`/`pr` in
their body, not a lifecycle status. Ask whether they meant to transition
the matching worktree — that is the artifact with the enum.
