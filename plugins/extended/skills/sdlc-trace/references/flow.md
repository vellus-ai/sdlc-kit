# sdlc-kit:trace — full flow

## Gap taxonomy

| Gap | Severity | Lens | Meaning |
|---|---|---|---|
| **Unimplemented PRD** | error | BA | PRD has no downstream `spec-*` wikilinking to it — product decided, engineering never picked up |
| **Dangling design** | error | BA | `spec-design` doesn't wikilink any PRD — designing something with no product rationale |
| **Missing tasks** | error | QA | `spec-tasks` exists but 0 task records — nobody queued the work |
| **Partial coverage** | warning | QA | Feature has some but not all of (PRD, requirements, design, tasks) — chain broken |
| **Orphan ADR** | info | BA | ADR not wikilinked from any other note — may be OK or means decision is divorced from consumers |
| **Orphan TRD** | info | BA | TRD not wikilinked — unreferenced NFR baseline, or downstream specs not updated yet |

Severities guide narration; the script reports all the same way.

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; script aborts with code 1.
2. **Python 3.10+** available.

## Flow

### Full report: `/sdlc-kit:trace`

1. Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-trace/scripts/trace.py" \
     --vault-root "<vault>" --action report
   ```
2. Parse the JSON.
3. Narrate in two passes:
   - **BA lens first.** Walk `unimplemented_prds` and `dangling_designs`. Each is a broken PRD↔spec link; suggest `/sdlc-kit:spec` or design wikilink edit.
   - **QA lens second.** Walk `features`; for each `coverage_status` of `partial`/`missing`, call out which piece is missing. For features with `tasks.task_count == 0`, flag nobody has queued work.
4. **Orphan ADRs/TRDs** get an informational paragraph — not necessarily broken.
5. Close with prioritized next step.

### Narrowed report: `/sdlc-kit:trace <slug>`

Same flow, pass `--slug <slug>`. Response narrows to one feature row; global gap lists still come through for context.

### Markdown output: `/sdlc-kit:trace --format markdown`

Pass `--format markdown`. JSON carries a single `markdown` field with rendered
table the user can paste into a note or review doc. Per-feature rows are dropped
in favour of the rendered text. Both formats produced by the **same generator**.

### After the report

Never writes. Follow-ups are other skills:
- PRD gap → `/sdlc-kit:prd new "<title>"`
- Requirements gap → `/sdlc-kit:spec new <slug>`
- Design gap → `/sdlc-kit:spec design <slug>`
- Tasks gap → `/sdlc-kit:spec tasks <slug>` or `/sdlc-kit:task new`
- Review gap → `/sdlc-kit:review new <pr-id>`
- Before acting on a gap, **cross-reference with `/sdlc-kit:impact <stem>`** to see downstream blast radius.

## Output contract

```json
// --format json (default)
{
  "status": "ok", "action": "report",
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
  "status": "ok", "action": "report",
  "vault_root": "/abs/path/.sdlc",
  "format": "markdown",
  "markdown": "# Traceability report\n\n…\n\n## Features\n\n| Slug | PRD refs | Requirements | Design | Tasks (count) | Reviews | Coverage |\n…",
  "errors": []
}
```

**`coverage_status`:**
- `complete` — has PRD ref, requirements, design, and tasks.
- `partial` — has at least one of (requirements, design, tasks) but not the full set (or no PRD ref).
- `missing` — none of the spec-* artifacts exist (slug only discovered via `04-specs/` subfolder).

**Exit codes:** `0` ok · `1` user error (not a vault, missing args) · `2` fatal.

## Guardrails

**Never:**
- Write, move, rename, or delete any file. Read-only. If user asks to "fix" a gap, point at the scaffold skill.
- Treat orphan ADR/TRD as *error* — informational. Some ADRs are genuinely one-off.
- Narrate every feature row when user only asked about a slug.
- Infer a feature slug not in the report. If user asks about an unknown slug, offer `/sdlc-kit:spec new <slug>`.
- Auto-invoke `/sdlc-kit:sync` after a report — sync writes; this skill shouldn't trigger one.

**Always:**
- Match the user's active conversation language.
- Run with absolute `--vault-root`.
- Before recommending a gap fix, recommend `/sdlc-kit:impact <stem>` first to see downstream blast radius.
- Quote exact paths from JSON.
- When `coverage_status: partial`, say which piece is missing — don't just say "partial".

## Examples

**Full report:**
```
User: /sdlc-kit:trace
AI:   [report] 3 features. BA-lens: 1 unimplemented PRD (`prd-analytics` — no downstream specs).
      QA-lens: 1 partial feature (`checkout` has requirements + design but no tasks).
      Orphan ADRs: `ADR-0042-orphan` (informational).
      Want me to scaffold tasks for `checkout` via `/sdlc-kit:spec tasks checkout`?
User: yes, but show me the impact first.
AI:   [defer to /sdlc-kit:impact checkout-design]
```

**Narrowed report:**
```
User: /sdlc-kit:trace login-google
AI:   [report --slug login-google] coverage=complete.
      PRD: prd-auth. Requirements, design, tasks all present (7 task records).
      1 review: pr-0042-login-google. Chain intact.
```

**Markdown output:**
```
User: /sdlc-kit:trace --format markdown
AI:   [report --format markdown] pasting:

      # Traceability report
      …
      | Slug         | PRD refs | Requirements | Design | Tasks (count) | Reviews              | Coverage |
      |--------------|----------|--------------|--------|---------------|----------------------|----------|
      | login-google | prd-auth | [x]          | [x]    | [x] (7)       | pr-0042-login-google | complete |
      | checkout     | prd-cart | [x]          | [x]    | [ ]           | —                    | partial  |
```

**Unknown slug:**
```
User: /sdlc-kit:trace foo-bar
AI:   [report --slug foo-bar] `foo-bar` wasn't discovered under 04-specs/.
      Want me to scaffold via `/sdlc-kit:spec new foo-bar`?
```

## See also

- `scripts/trace.py` — read-only report generator.
- `/sdlc-kit:sync` — vault-wide validation + index regeneration.
- `/sdlc-kit:impact` — downstream change impact.
- `/sdlc-kit:prd`, `/sdlc-kit:spec`, `/sdlc-kit:task`, `/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:review`.
