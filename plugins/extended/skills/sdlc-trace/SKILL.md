---
name: sdlc-trace
description: |
  Use when the user wants a requirement-to-artifact traceability matrix across
  the SDLC vault — "trace coverage", "traceability", "requirement coverage",
  "which PRDs have no implementation", "which designs have no PRD upstream",
  "show the spec/task/review chain for <feature>"; or in pt-BR "matriz de
  rastreabilidade", "cobertura de requisitos", "quais requisitos não têm
  implementação", "quais ADRs estão órfãos". Typical triggers are
  /sdlc-kit:trace, /sdlc-kit:trace <slug>, /sdlc-kit:trace --format markdown.
  This skill is **read-only**: it walks the vault, indexes frontmatter and
  wikilinks, and reports the coverage chain PRD → spec-requirements →
  spec-design → spec-tasks → tasks → review, plus supporting ADRs/TRDs.
  It **never writes** any artifact. The skill is co-authored by two lenses — a
  **Requirements Engineer / BA** (owns the PRD↔spec chain: does every PRD have
  a spec? does every spec wikilink back to its PRD?) and a **QA Lead** (owns
  the spec↔task↔review chain: does every spec-tasks have task records? does
  every merged feature have a review?). Invoke /sdlc-kit:trace to surface gaps
  before a release review, before a quarterly audit, after a big planning
  round, or whenever the team is unsure which requirements actually shipped.
  Do not invoke to *fix* the gaps — the skill reports; creating the missing
  artifacts belongs to /sdlc-kit:prd, /sdlc-kit:spec, /sdlc-kit:task,
  /sdlc-kit:adr, /sdlc-kit:trd or /sdlc-kit:review.
---

# sdlc-kit:trace

**Requirement↔Artifact traceability, read-only.**

Walks every markdown under the vault (excluding `.sdlc-kit/`, `_templates/`,
hidden folders), indexes frontmatter and wikilinks, and reports the chain the
industry expects a mature SDLC to keep intact:

```
PRD (01-planning)
 └─ spec-requirements (04-specs/<slug>/)
     └─ spec-design (04-specs/<slug>/)
         └─ spec-tasks (04-specs/<slug>/)
             └─ task records
                 └─ worktree / branch (05-development)
                     └─ review (07-retrospectives/reviews)
ADR (02-architecture/ADR) ── supports design decisions
TRD (02-architecture/trd) ── constrains designs
```

A **gap** is any artifact that should be referenced by another but isn't. The
skill does not fix gaps — it surfaces them so the user can invoke the correct
scaffolder (`/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:task`, etc.).

---

## Authoring lenses

Every report is co-authored by two lenses, in this order:

1. **Requirements Engineer / BA** — owns the PRD↔spec chain. For every PRD,
   is there at least one spec-requirements that wikilinks back? For every
   spec-design, is there an upstream PRD? These are the *did we document what
   we're building?* questions.
2. **QA Lead** — owns the spec↔task↔review chain. For every spec-tasks, is
   there a matching set of task records? For every shipped feature, is there
   a review? These are the *did we verify what we built?* questions.

When you narrate the output, call out which lens each gap belongs to so the
user knows who to loop in.

---

## Gap taxonomy

| Gap | Severity | Lens | Meaning |
|---|---|---|---|
| **Unimplemented PRD** | error | BA | PRD has no downstream `spec-*` wikilinking to it — product decided something, engineering never picked it up |
| **Dangling design** | error | BA | `spec-design` doesn't wikilink to any PRD — engineering is designing something with no product rationale |
| **Missing tasks** | error | QA | `spec-tasks` exists but has 0 task records (no task notes with matching `slug`, no checkboxes in the body) — nobody's queued the work |
| **Partial coverage** | warning | QA | Feature has some but not all of (PRD, requirements, design, tasks) — chain is broken somewhere |
| **Orphan ADR** | info | BA | ADR not wikilinked from any other note — may be OK (some ADRs document one-off decisions) but probably means the decision is divorced from its consumers |
| **Orphan TRD** | info | BA | TRD not wikilinked from any other note — either unreferenced NFR baseline, or we haven't updated downstream specs to inherit yet |

Severities are guidance for how to narrate the report; the script reports all
of them the same way.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:trace`, `/sdlc-kit:trace <slug>`, or
  `/sdlc-kit:trace --format markdown`.
- The user asks "what's the traceability of feature X?", "which PRDs don't
  have any specs?", "quais requisitos ainda não viraram task?", "qual a
  cobertura de requisitos?".
- Before a release review, quarterly audit, or compliance export — the matrix
  is the auditor's artifact.
- After a big planning round, to check whether every PRD got at least a
  spec-requirements stub.

**Do not** invoke when:

- The user wants you to *create* the missing artifacts — that's
  `/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:task`, `/sdlc-kit:adr`,
  `/sdlc-kit:trd` or `/sdlc-kit:review`. This skill is strictly read-only.
- The user wants the global vault health (broken wikilinks, stale dates,
  duplicate titles) — that's `/sdlc-kit:sync`. Traceability is a narrower
  question.
- The user wants to know *which other artifacts a change will hit* — that's
  `/sdlc-kit:impact`. Impact and trace are related but not the same: trace
  asks "is the chain complete?", impact asks "if I change this, what else
  moves?".
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; the script aborts
   with exit code 1 otherwise.
2. **Python 3.10+** available.

---

## Flow

### Full report: `/sdlc-kit:trace`

1. Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-trace/scripts/trace.py" \
     --vault-root "<vault>" --action report
   ```
2. Parse the JSON payload.
3. Narrate the findings in two passes:
   - **BA lens first.** Walk `unimplemented_prds` and `dangling_designs`.
     Each one is a broken PRD↔spec link; suggest `/sdlc-kit:spec` or an edit
     to the design to wikilink its PRD.
   - **QA lens second.** Walk the `features` list; for each `coverage_status`
     of `partial` or `missing`, call out which piece is missing and which
     skill would scaffold it. For features whose `tasks.task_count` is 0,
     flag that nobody has queued the work.
4. **Orphan ADRs/TRDs** get an informational paragraph at the end — they're
   not necessarily broken, but worth acknowledging.
5. Close with a prioritized next step: usually either "scaffold the missing
   spec for PRD X via `/sdlc-kit:spec`" or "retarget the dangling design
   `<stem>` to wikilink its PRD".

### Narrowed report: `/sdlc-kit:trace <slug>`

Same flow, but pass `--slug <slug>`. The response narrows to a single feature
row; global gap lists (orphan ADRs, unimplemented PRDs) still come through so
the user has context.

### Markdown output: `/sdlc-kit:trace --format markdown`

Pass `--format markdown`. The JSON payload then carries a single `markdown`
field with a rendered table the user can paste into a note or a review doc.
The structured per-feature rows are dropped in favour of the rendered text —
both formats are produced by the **same report generator**, just rendered
differently. If the user wants both, call the script twice.

### After the report

This skill never writes. Its follow-ups are always other skills:

- PRD gap → `/sdlc-kit:prd new "<title>"`
- Requirements gap → `/sdlc-kit:spec new <slug>` (scaffolds the full trio)
- Design gap → `/sdlc-kit:spec design <slug>`
- Tasks gap → `/sdlc-kit:spec tasks <slug>` or `/sdlc-kit:task new`
- Review gap → `/sdlc-kit:review new <pr-id>`
- Before acting on a gap, **cross-reference with `/sdlc-kit:impact <stem>`** to
  see every downstream artifact the change will touch.

---

## Output contract

```json
// --format json (default)
{
  "status": "ok",
  "action": "report",
  "vault_root": "/abs/path/.sdlc",
  "format": "json",
  "features": [
    {
      "slug": "login-google",
      "prd_refs": ["prd-auth"],
      "requirements": {"exists": true, "path": "04-specs/login-google/login-google-requirements.md"},
      "design":       {"exists": true, "path": "04-specs/login-google/login-google-design.md"},
      "tasks":        {"exists": true, "path": "04-specs/login-google/login-google-tasks.md", "task_count": 7},
      "reviews":      ["pr-0042-login-google"],
      "coverage_status": "complete"
    }
  ],
  "orphan_adrs":        ["ADR-0042-orphan"],
  "orphan_trds":        [],
  "dangling_designs":   [],
  "unimplemented_prds": ["prd-analytics"],
  "errors": []
}

// --format markdown
{
  "status": "ok",
  "action": "report",
  "vault_root": "/abs/path/.sdlc",
  "format": "markdown",
  "markdown": "# Traceability report\n\n…\n\n## Features\n\n| Slug | PRD refs | Requirements | Design | Tasks (count) | Reviews | Coverage |\n…",
  "errors": []
}
```

**`coverage_status`:**
- `complete` — has a PRD ref, requirements, design, and tasks.
- `partial` — has at least one of (requirements, design, tasks) but not the
  full set (or no PRD ref).
- `missing` — none of the spec-* artifacts exist for this slug (the slug was
  only discovered via the subfolder name under `04-specs/`).

**Exit codes:** `0` ok · `1` user error (not a vault, missing args) · `2` fatal
(permission denied, IO).

---

## Guardrails

**Never:**
- Write, move, rename, or delete any file. This skill is strictly read-only.
  If the user asks you to "fix" a gap, point them at the scaffold skill —
  don't call it yourself from inside `/sdlc-kit:trace`.
- Treat an orphan ADR or orphan TRD as an *error* without qualification —
  it's informational. Some ADRs are genuinely one-off decisions with no
  consumers yet; flag but don't demand a fix.
- Narrate every feature row when the user only asked about a slug — keep the
  scope tight.
- Infer a feature slug that's not in the report. If the user asks about a
  slug the script didn't discover, say so and ask whether they want to
  scaffold it via `/sdlc-kit:spec new <slug>`.
- Auto-invoke `/sdlc-kit:sync` after a report. Sync is a write operation and
  this skill shouldn't trigger one just to refresh the index.

**Always:**
- Match the user's active conversation language when narrating.
- Run the script with an absolute `--vault-root`.
- Before recommending a gap fix, recommend `/sdlc-kit:impact <stem>` first so
  the user sees the downstream blast radius of the change they're about to
  make.
- Quote exact paths from the JSON when pointing the user at a specific note.
- When `coverage_status` is `partial`, say which piece is missing — don't just
  say "partial" and move on.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active
> conversation language in every user-facing line.

**Full report:**
```
User: /sdlc-kit:trace
AI:   [report] 3 features discovered. BA-lens findings: 1 unimplemented PRD
      (`prd-analytics` — no downstream specs). QA-lens findings: 1 partial
      feature (`checkout` has requirements + design but no tasks). Orphan
      ADRs: `ADR-0042-orphan` (informational). Want me to scaffold the
      missing tasks for `checkout` via `/sdlc-kit:spec tasks checkout`?
User: yes, but show me the impact first.
AI:   [defer to /sdlc-kit:impact checkout-design]
```

**Narrowed report:**
```
User: /sdlc-kit:trace login-google
AI:   [report --slug login-google] login-google: coverage=complete.
      PRD: prd-auth. Requirements, design, tasks all present (7 task records).
      1 review: pr-0042-login-google. Chain is intact.
```

**Markdown output:**
```
User: /sdlc-kit:trace --format markdown
AI:   [report --format markdown] pasting the rendered matrix:

      # Traceability report
      …
      | Slug          | PRD refs  | Requirements | Design | Tasks (count) | Reviews              | Coverage |
      |---------------|-----------|--------------|--------|---------------|----------------------|----------|
      | login-google  | prd-auth  | [x]          | [x]    | [x] (7)       | pr-0042-login-google | complete |
      | checkout      | prd-cart  | [x]          | [x]    | [ ]           | —                    | partial  |
```

**Narrowing to an unknown slug:**
```
User: /sdlc-kit:trace foo-bar
AI:   [report --slug foo-bar] `foo-bar` wasn't discovered under 04-specs/.
      Want me to scaffold it via `/sdlc-kit:spec new foo-bar`?
```

---

## See also

- `scripts/trace.py` — read-only report generator.
- `/sdlc-kit:sync` — vault-wide validation + `_INDEX.md` regeneration (writes).
- `/sdlc-kit:impact` — downstream change impact for a specific note.
- `/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:task`, `/sdlc-kit:adr`,
  `/sdlc-kit:trd`, `/sdlc-kit:review` — the scaffolders that *fix* the gaps
  this skill reports.
