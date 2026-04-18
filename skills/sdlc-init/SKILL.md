---
name: sdlc-init
description: |
  Use when the user wants to initialize an SDLC (Spec-Driven Development)
  vault in a Git project. English triggers: `/sdlc-kit:init`,
  "set up the SDLC Kit in this project", "initialize SDLC Kit",
  "bootstrap the vault". pt-BR triggers: "criar o vault SDLC",
  "inicializar o SDLC Kit", "começar a usar o SDLC Kit neste projeto".
  Driven by an **onboarding utility** — no persona interview, just a
  one-question greenfield/brownfield gate and deterministic scaffold. Runs a
  minimal, low-friction onboarding: asks ONE required question (greenfield
  vs brownfield), auto-detects repo root / owner / remote URL, and scaffolds
  `.sdlc/` with 8 canonical phases (00-steering, 01-planning,
  02-architecture, 03-domain, 04-specs, 05-development, 06-design-system,
  07-retrospectives), CLAUDE.md doctrine, _INDEX.md, dashboard HTML,
  marker.json, and SQLite tracker. Never overwrites files without explicit
  `--force` confirmation. Intentionally does NOT ask for tech stack,
  bounded contexts, design system, or worktree preferences — those belong
  to dedicated later skills (`/sdlc-kit:steer tech`, ADRs,
  `/sdlc-kit:domain`, etc.). For greenfield projects, optionally bootstraps
  `git init` + GitHub repo via `gh repo create`. Appends a vault pointer to
  the project root CLAUDE.md and runs the initial librarian scan. Do not
  invoke without explicit user intent.
---

# sdlc-kit:init

Initializes an SDLC vault in `.sdlc/` inside the current Git repository.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:init`
- The user asks to "criar o vault SDLC", "inicializar SDLC Kit", "começar a usar SDLC Kit neste projeto"
- The user wants to adopt an existing project into SDLC Kit (use `--adopt` — see `references/adopt.md`)

**Do not** invoke when:
- The user only wants to understand what the plugin does (explain, don't scaffold)
- cwd is already inside an active vault and the user did not ask to re-init
- Called from a secondary git worktree (always init from the main worktree)

---

## Pre-checks

Run in order and stop on the first failure:

1. **Write permission in cwd.** Try `touch .sdlc-kit-permcheck && rm .sdlc-kit-permcheck`. Abort on failure.
2. **Python 3.10+ available.** `python3 --version` — if missing, ask the user to install.
3. **Run the detector:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-init/scripts/detect.py"
   ```
   Parse the JSON. Relevant fields: `is_git_repo`, `repo_root`, `basename`, `owner_display`, `remote_https_url`, `has_sdlc`, `gh_cli_available`, `suggested_mode`.
4. **If `has_sdlc == true`** (vault already exists), short-circuit the interview entirely. Run `scaffold.py --dry-run` and offer the user:
   - `(a)` Fill in missing files only — idempotent, default
   - `(b)` Do nothing
   - `(c)` Recreate from scratch — **destructive**, requires `--force` and explicit confirmation

---

## The interview (1 required question)

Phrase every prompt in whatever language the user is using in the current conversation. Never ask about tech stack, bounded contexts, design system, or worktrees — those belong to later skills.

### Q1 — Greenfield or brownfield?

Prompt example (adapt to the user's language):

> "Is this a new or existing project?
>   [b] brownfield — I already have code/repo (default)
>   [g] greenfield — starting from scratch"

Default follows `detect.suggested_mode`. If the user just presses Enter, use the detected mode.

---

### Branch A — Brownfield flow

**Pre-condition:** must be inside a git repo (`is_git_repo == true`). If not, abort with a message like:

> "You chose brownfield but this directory is not a Git repository. Run `git init` first, or re-invoke and choose greenfield."

Show auto-detected values and **one confirmation gate**:

```
Detected:
  Project:  <basename>
  Owner:    <owner_display>        (from git config)
  Repo:     <remote_https_url>     (from git remote)

Create the vault with these values?
  [Enter] yes    [e] edit    [s] skip all (use placeholders)
```

- **`Enter` / `yes` / `y`** → jump straight to scaffold with detected values.
- **`e` / `edit`** → walk through each field (project, owner, repo). For each, show `[<current>]:` and accept:
  - `Enter` → keep current
  - `-` or `x` → clear field
  - typed text → override
- **`s` / `skip`** → pass empty strings for all optional fields. The vault CLAUDE.md will render helpful "TBD — run `/sdlc-kit:steer tech`" notes in place of empty values.

---

### Branch B — Greenfield flow

1. **Project name?** Show `[<basename>]:` as default; Enter accepts.
2. **Create a GitHub repo now?** Offer only if `gh_cli_available == true`. Default `N`.
   - If `y`:
     - **Visibility** → `[priv] privado (default)` | `[pub] público`
     - **Namespace** → default to the user's personal GitHub account. If the user has orgs configured, they may type `<org>/<name>` explicitly.
     - Execute:
       ```bash
       git init                          # only if !is_git_repo
       git branch -M main                # only if !is_git_repo
       gh repo create "<namespace>/<name>" --<visibility> --source=. --remote=origin
       ```
     - Re-run `detect.py` to refresh `remote_https_url`.
   - If `N`:
     - Still run `git init` if `!is_git_repo` (scaffold requires a git root).
3. Proceed to scaffold. Owner comes from `detect.owner_display`; repo URL may be empty.

---

## Execution

After the interview:

1. **Dry-run first (always):**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-init/scripts/scaffold.py" \
     --vault-root "<repo_root>/.sdlc" \
     --project-name "<name>" \
     --owner "<owner>" \
     --repo-url "<url-or-empty>" \
     --dry-run
   ```
   If the user already confirmed in Q1/gate, silently move to step 2 using the summary. Otherwise show `created/skipped/updated` counts and ask for final approval.

2. **Real scaffold** (no `--dry-run`). The script:
   - Copies `assets/vault-tree/` → `.sdlc/` applying placeholders
   - Writes `.sdlc/.sdlc-kit/marker.json` with `{version, created, project_name, owner, repo_url}`
   - Preserves existing files (silent skip) unless `--force`

3. **Initialize SQLite:**
   ```bash
   cd .sdlc && sdlc-kit init-db
   ```

4. **First librarian scan:**
   ```bash
   cd .sdlc && sdlc-kit scan
   ```

5. **Append to the project root CLAUDE.md** (append-only — never rewrite). Detect the `## SDLC Vault` header to skip if already present. Write the block in the conversation's active language; default template in English:

   ```markdown

   ## SDLC Vault

   This project uses the **SDLC Kit**. Before starting any task:

   - Read `.sdlc/CLAUDE.md` — vault doctrine (frontmatter schema, conventions)
   - Consult `.sdlc/_INDEX.md` — live index (regenerated by the librarian)

   Main commands: `/sdlc-kit:steer`, `/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:adr`, `/sdlc-kit:dash`
   ```

   If there is no root CLAUDE.md, create a minimal one containing this block.

6. **Final report** (concise, in the conversation's language). Show:
   - Vault path: `<repo_root>/.sdlc/`
   - Files created / preserved (from scaffold JSON summary)
   - Next steps:
     1. `/sdlc-kit:steer tech` — technical principles and stack
     2. `/sdlc-kit:steer product` — product vision
     3. `/sdlc-kit:adr new "<first decision>"` — record critical decisions
     4. `/sdlc-kit:prd new "<first initiative>"` — first PRD
     5. `/sdlc-kit:dash` — open the dashboard in the browser

---

## Guardrails

**Never:**
- Ask about tech stack, bounded contexts, design system, or worktrees — those are out of scope for init
- Overwrite an existing vault CLAUDE.md (sovereign — user's property)
- Overwrite `_INDEX.md` manually (librarian owns it)
- Run `--force` without explicit user confirmation
- Scaffold outside a Git repository (except in greenfield, which initializes it)
- Create `.sdlc/` inside `$HOME`, `/`, `C:/`, or less than 2 levels below `$HOME`
- Auto-commit — the user decides when to commit

**Always:**
- Match the user's active conversation language in every confirmation, error, and report line
- Run `--dry-run` first and summarize the plan
- Suggest `.gitignore` entries for `.sdlc/.sdlc-kit/db.sqlite` and `*-errors.log`
- Treat script stdout as structured JSON — never mix free-text logs into it
- If any step fails, stop and report the failing step clearly

---

## Script output contract

Both `detect.py` and `scaffold.py` emit a single JSON object on stdout. Diagnostics go to stderr.

`scaffold.py` output:
```json
{
  "status": "ok" | "dry-run" | "error",
  "vault_root": "/abs/path/.sdlc",
  "files_created": ["00-steering/product.md", ...],
  "files_skipped": ["CLAUDE.md"],
  "files_updated": [],
  "errors": [],
  "summary": { "created": 42, "skipped": 3, "updated": 0 }
}
```

Exit codes:
- `0` — success (or dry-run)
- `1` — user error (missing arg, git not available, path too shallow, etc.)
- `2` — fatal (permission denied, assets missing)

---

## Examples

**Brownfield, zero friction (ideal case):**
```
User: /sdlc-kit:init
AI:   [pre-checks] [detect.py] shows summary → user hits Enter
      [scaffold] [init-db] [scan] [append root CLAUDE.md]
AI:   "Vault created at .sdlc/ (42 files). Next steps: ..."
```

**Greenfield, with GitHub repo:**
```
User: /sdlc-kit:init
AI:   "Is this a new or existing project? [b/g]"
User: g
AI:   "Project name? [my-folder]"
User: my-new-app
AI:   "Create a GitHub repo? [y/N]"
User: y
AI:   "Visibility? [priv/pub]"
User: [Enter]
AI:   [git init] [gh repo create <user>/my-new-app --private] [scaffold] [init-db] [scan]
AI:   "Repo github.com/<user>/my-new-app and vault created. Next steps: ..."
```

**Re-init on an existing vault (idempotent repair):**
```
User: /sdlc-kit:init
AI:   "Found existing .sdlc/. Dry-run shows 2 templates missing in 04-specs/_templates/. Fill them in? (y/n)"
User: y
AI:   [scaffold without --force, fills only missing files]
```

**Brownfield chosen but no git repo:**
```
User: /sdlc-kit:init
AI:   "Is this a new or existing project? [b/g]"
User: b
AI:   "You chose brownfield but this directory is not a Git repository.
       Run `git init` first, or re-invoke and choose greenfield."
```

---

## See also

- `scripts/detect.py` — auto-detection helper (JSON on stdout)
- `scripts/scaffold.py` — idempotent scaffold
- `references/adopt.md` — adopting a legacy project
- `references/frontmatter-schema.md` — frontmatter schema
- `docs/decisions/ADR-0001-estrutura-canonica.md` — canonical 8-folder structure
- `docs/decisions/ADR-0002-skills-inventory.md` — 21-skill inventory
