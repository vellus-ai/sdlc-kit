# sdlc-kit:worktree — full flow

## Kinds, paths and templates

| Kind       | Type slug | Cardinality | Path                                   | Template                     |
|------------|-----------|-------------|----------------------------------------|------------------------------|
| `worktree` | `worktree` | Collection | `05-development/worktrees/<slug>.md`   | `_templates/worktree.md.tpl` |
| `branch`   | `branch`   | Collection | `05-development/branches/<slug>.md`    | `_templates/branch.md.tpl`   |

## Lifecycle

### `worktree`
```
active  →  merged
active  →  abandoned
```
- `active` — scaffolded. Git worktree directory may or may not exist on disk yet.
- `merged` — PR merged, branch deleted, worktree directory removed. Terminal.
- `abandoned` — work discarded; worktree removed, branch deleted or stale. Terminal. Body should explain *why*.

### `branch`
No formal status enum. Tracks:
- `branch_type` (`feat` / `fix` / `chore` / `refactor` / `docs` / `test`)
- `base` (usually `main`)
- `pr` (PR number/URL once opened)
- `ci_status` (`passing` / `running` / `failed` / `pending` — edit in body; no `transition` action)

Script refuses `transition` for kind `branch` with exit 1. Update body instead.

## Flow

### 1. Pre-flight
- Run `list` first. **Never scaffold over an existing record without `--force`**.
- Read vault's `CLAUDE.md` — may pin branch naming, base policies, merge strategy.

### 2. Scaffold
Run `scripts/worktree.py --action scaffold` with:
- `--kind {worktree|branch}`
- `--slug <slug>` (required; `[a-z0-9][a-z0-9-]*`)
- `--title "<human title>"` (required)
- `--owner <handle>` (optional)

The script validates slug, refuses overwrite without `--force`, substitutes template placeholders.

### 3. Interview (per kind)

| Kind       | Must-fill sections |
|------------|--------------------|
| `worktree` | Branch name, base SHA, local path, linked feature/task, agent_active checkbox, history entry |
| `branch`   | Branch name, type, base, PR link (if open), linked task(s), CI status, main commits table |

Every missing field is filled or explicitly marked `— N/A —` with a 1-line justification.

### 4. Cross-link
- A `worktree` record's *References* must wikilink its matching `branch` record (`[[<branch-slug>]]`) and vice-versa if both exist.
- Both wikilink the feature design (`[[<feature>-design]]`) and relevant tasks (`[[<feature>-tasks#TASK-NNN]]`).

### 5. Transition (worktree only)
```
scripts/worktree.py --action transition --kind worktree --slug <slug> --to merged
scripts/worktree.py --action transition --kind worktree --slug <slug> --to abandoned
```
Idempotent.

## Pre-merge checklist (hard gate for `--to merged`)

Block unless **all** are true — duo sign-off (Senior SWE confirms first three; Release Engineer last three):

- [ ] CI is green on the final commit of the branch (SWE).
- [ ] PR has been approved and **actually merged** into the base branch (Release).
- [ ] Local feature branch has been deleted (`git branch -d <branch>`) (SWE).
- [ ] Worktree directory has been removed (`git worktree remove <path>`) (SWE).
- [ ] `/sdlc-kit:sync` has been run so `_INDEX.md` reflects the new state (Release).
- [ ] Any follow-up issues have a corresponding task or TRD entry (Release).

If any unchecked: **do not transition**. Keep `active` and list the missing items.

## Output contract

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`, `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`, `new_status`.

Exit codes: `0` ok/dry-run, `1` user error (invalid kind/slug/status, missing arg, transition on `branch`), `2` fatal.

## Guardrails

**Never:**
- Delete a worktree or branch `.md` record. Use `abandoned` and record why.
- Rename a slug — backlinks break. Scaffold a new record and note replacement in the old body.
- Call `transition` on kind `branch` — script refuses. Edit body (CI status, commits) directly.
- Promote to `merged` without the full pre-merge checklist passing and both lenses signing off.
- Scaffold over existing without `--force` and explicit reason.

**Always:**
- Prefer `abandoned` over silent deletion for worktrees that won't merge.
- Keep `updated` honest — `transition` refreshes automatically.
- Run `/sdlc-kit:sync` after any scaffold or transition.
- Mirror user's chat language in body; keep frontmatter and template scaffolding in English.

## Examples

### Open a new worktree for a feature
```
scripts/worktree.py --action scaffold --kind worktree \
  --slug feat-login --title "Login feature" --owner milton
```
Interview to fill branch name (e.g. `feat/login`), base SHA, local path (`../project-feat-login`), linked feature/task.

### Register the matching branch record
```
scripts/worktree.py --action scaffold --kind branch \
  --slug feat-login --title "feat/login"
```
Fill `branch_type: feat`, base, CI status. Cross-link the worktree record.

### List every open worktree
```
scripts/worktree.py --action list --kind worktree
```

### Mark merged (after pre-merge checklist passes)
```
scripts/worktree.py --action transition --kind worktree \
  --slug feat-login --to merged
```
Then `/sdlc-kit:sync`.

### Smell: transition on a branch
If user asks to "mark branch `feat-login` as merged" via `transition --kind branch`,
refuse. Branches carry `ci_status`/`pr` in body, not lifecycle. Suggest transitioning
the matching worktree instead.
