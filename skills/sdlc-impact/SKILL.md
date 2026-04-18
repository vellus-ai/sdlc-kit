---
name: sdlc-impact
description: |
  Use when the user wants a change-impact analysis over the vault's wikilink
  graph. English triggers: `/sdlc-kit:impact`, `/sdlc-kit:impact <seed>`,
  "what breaks if I deprecate this?", "blast radius",
  "what depends on this?", "dependents of", "dependencies of",
  "who links to this note",
  "check the blast radius before I change ADR-0007",
  "who still references the mobile-client TRD?",
  "what does the login-google spec depend on?". pt-BR triggers:
  "análise de impacto", "raio de impacto", "o que quebra se eu mudar",
  "o que depende disso", "quem depende disso", "antes de deprecar",
  "antes de renomear", "antes de mover". Driven by a **Software Architect**
  persona — assesses design-time coupling revealed by the graph, flags
  accidental duplication vs healthy inheritance, and advises on migration
  ordering before destructive actions. Reads every `.md` under the vault
  (skipping `.sdlc-kit/`, `_templates/`, hidden folders), builds a directed
  graph of `[[wikilinks]]`, and walks it with a bounded BFS from a seed
  note. Backward (default) answers "what depends on this?"; forward answers
  "what does this depend on?"; `both` takes the union. The script is
  read-only and stdlib-only — it never writes to the vault and never shells
  out. The graph reflects only wikilinks; plain-text and code references are
  invisible, so always cross-check with grep / code search before a
  destructive action. Do not invoke for free-text concept search, for
  scaffolding or transitioning notes (use the type-specific skill such as
  `/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:spec`), or when cwd is not
  inside a `.sdlc-kit` vault.
---

# sdlc-kit:impact

Read-only change-impact analysis over the vault's `[[wikilink]]` graph.

Given a seed note, the skill walks the graph and reports every artifact that
depends on it (backward) or that it depends on (forward), up to a bounded
depth. Answers questions like:

- "What breaks if I deprecate `ADR-0007-oauth`?"
- "Who still references `TRD-mobile-client` before I retire it?"
- "What does the `login-google-design` spec transitively depend on?"
- "Before I rename this feature slug, what else do I have to touch?"

---

## Persona duo

Every run is co-authored by two lenses. Mention them when reporting:

| Lens | Concern |
|---|---|
| **Senior Software Engineer** (refactor / blast-radius) | Operational impact of the proposed change. How many artifacts must move? Which of them are in-flight? Is the change reversible? What's the migration order? |
| **Software Architect** (design-time coupling) | Structural coupling revealed by the graph. Are the dependents *inheriting* from the seed (healthy) or *duplicating* it (smell)? Are there backward edges that point the wrong way in the dependency pyramid (e.g. a PRD pointing down into a spec)? Is the seed over-referenced — should we split it? |

The engineer tells the user **what will cost to change**; the architect tells
the user **whether the cost is signal or noise**.

---

## What the graph represents (and doesn't)

- **Represents**: every `[[target]]` wikilink in the body of any `.md` under
  the vault, minus `.sdlc-kit/`, `_templates/`, hidden folders. Aliases
  (`[[target|display]]`) and anchors (`[[target#heading]]`) are normalized to
  the target stem. Dangling wikilinks (targets that don't resolve to a file)
  are dropped.
- **Does not represent**: plain-text mentions ("the OAuth ADR"), code-level
  references (imports, SDK usage, config keys), external links, wikilinks
  inside frontmatter (e.g. `parent: "[[..]]"` — those are metadata, not body
  edges).

**Implication**: the graph is a *documentation* view, not a *code* view.
Before a destructive action (rename / deprecate / delete), always
cross-check with `grep` or a code search so plain-text and code references
don't become silent orphans.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:impact`, `/sdlc-kit:impact <seed>`, or says
  "check the impact / blast radius / dependents / dependencies of X", or
  the pt-BR equivalents ("análise de impacto", "raio de impacto", "o que
  quebra se eu mudar", "o que depende disso", "quem depende disso", "antes
  de deprecar / renomear / mover").
- Before **deprecating** an ADR, TRD, API contract, design-system token, or
  design-system component — find every document declaring compliance or
  inheriting from it.
- Before **renaming / moving** a feature slug (spec folder, ADR filename).
  The skill surfaces every downstream document whose wikilinks must be
  retargeted.
- Before **merging a worktree** that touches an aggregate with many
  consumers — confirms the change doesn't silently invalidate a PRD or
  retrospective that references the aggregate.
- When the user wants a **pre-mortem** on a planned refactor — "before I
  restructure the auth domain, who depends on it?".

**Do not** invoke when:

- The user wants free-text / concept search across the vault (no wikilink
  needed) — this skill only follows wikilink edges.
- The user wants to scaffold or transition a note (use `/sdlc-kit:adr`,
  `/sdlc-kit:trd`, `/sdlc-kit:spec`, `/sdlc-kit:prd`, etc.).
- The user wants full **code** impact — this skill reports
  *document-graph* impact only. Combine with a grep / code search for the
  full picture.
- cwd is not inside a vault (no `.sdlc-kit/marker.json`).

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available (the script uses `from __future__` + PEP 604
   unions).
3. **Seed exists.** Run the analysis; the script itself refuses a missing
   or ambiguous seed with exit code 1 and a clear error.

---

## Flow

### Invoke: `/sdlc-kit:impact <seed>` (or the natural-language form)

1. **Pick the direction.** Default is `backward` ("who depends on the
   seed?"). Use `forward` when the user asks "what does this depend on?"
   and `both` when they want the union.
2. **Pick the depth.** Default is 3. Use 1 when the user only wants
   immediate neighbours. Use up to 10 for deep traces. Anything above 10 is
   silently clamped.
3. **Run the analyzer.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-impact/scripts/impact.py" \
     --vault-root "<vault>" --action analyze \
     --seed "<seed>" \
     [--direction backward|forward|both] \
     [--depth N] \
     [--format json|markdown]
   ```
4. **Present the result.** Summarize the blast radius. The engineer lens
   names the number of dependents and groups them by type; the architect
   lens comments on whether the shape is healthy (tight cluster of
   inheritors) or a smell (a single seed referenced by dozens of unrelated
   docs — candidate for split).
5. **Always remind the user** that the graph is wikilink-only — suggest a
   complementary grep / code search if the action is destructive.

### Seed resolution

The script accepts a stem, a frontmatter `slug`, or a frontmatter `title`,
in that order of precedence. If the seed is ambiguous (multiple files share
the same stem/slug/title), the script exits with code 1 and lists the
candidates — the user must disambiguate with a more specific stem.

---

## Output contract

```json
{
  "status": "ok",
  "action": "analyze",
  "vault_root": "/abs/path/.sdlc",
  "seed": "ADR-0007-oauth",
  "seed_path": "02-architecture/ADR/ADR-0007-oauth.md",
  "direction": "backward",
  "depth": 3,
  "nodes": [
    {"stem": "ADR-0007-oauth",         "doc_type": "adr",         "depth": 0, "path": "02-architecture/ADR/ADR-0007-oauth.md"},
    {"stem": "login-google-design",    "doc_type": "spec-design", "depth": 1, "path": "04-specs/login-google/login-google-design.md"},
    {"stem": "login-google-tasks",     "doc_type": "spec-tasks",  "depth": 2, "path": "04-specs/login-google/login-google-tasks.md"},
    {"stem": "pr-0001-login-google",   "doc_type": "review",      "depth": 2, "path": "07-retrospectives/reviews/pr-0001-login-google.md"}
  ],
  "edges": [
    {"from": "login-google-design",  "to": "ADR-0007-oauth"},
    {"from": "login-google-tasks",   "to": "login-google-design"},
    {"from": "pr-0001-login-google", "to": "login-google-design"}
  ],
  "summary": {
    "total_dependents": 3,
    "by_type": {"spec-design": 1, "spec-tasks": 1, "review": 1},
    "unreachable": false
  },
  "errors": []
}
```

When `--format markdown`, the same object is returned with an extra
`markdown` field containing a human-readable tree grouped by depth plus a
by-type breakdown and an edge table.

**Exit codes:** `0` ok · `1` user error (seed not found, ambiguous seed,
not a vault, empty vault) · `2` fatal (permission denied, IO error).

---

## Guardrails

**Never:**
- Present the graph as the *full* impact picture. It captures wikilinks
  only; plain-text mentions and code references stay invisible. Always
  remind the user to cross-check with grep / code search before a
  destructive change.
- Follow wikilinks from inside frontmatter as graph edges — only the body
  is walked.
- Write to the vault. The skill is read-only. If the user asks to mutate
  something based on the findings, hand off to the relevant skill
  (`/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:spec`) — do not edit
  anything yourself from within this flow.
- Silently expand the depth past 10. The script clamps; say so in the
  report when the user asked for a larger depth.
- Treat "no dependents reached" as proof of isolation. A note with zero
  inbound wikilinks may still be referenced by plain text or by code.

**Always:**
- Match the user's active conversation language.
- State the direction, depth, and seed at the top of every answer so the
  user can evaluate the scope of the report.
- Group dependents by `doc_type` in the summary — it's usually the most
  actionable slice ("3 specs + 2 reviews depend on this ADR").
- Offer the next step: either "shall we deprecate X and retarget the
  dependents?" (hand off to the type-specific skill) or "want me to widen
  the depth / flip direction?".
- Cap the answer at the actual data. If `total_dependents == 0` at the
  chosen depth, say so plainly and suggest widening the depth rather than
  speculating.

---

## Examples

> Examples below are in English. In a real session, mirror the user's
> active conversation language in every user-facing line.

**Backward 2 levels from an ADR (before deprecation):**
```
User: /sdlc-kit:impact ADR-0007-oauth --depth 2
AI:   [analyze --seed ADR-0007-oauth --direction backward --depth 2]
AI:   "Seed: ADR-0007-oauth (adr). Backward walk, depth 2.
       3 dependents — 1 spec-design (login-google-design), 1 spec-tasks
       (login-google-tasks), 1 review (pr-0001-login-google).
       Engineer lens: before deprecating, retarget login-google-design to
       the successor ADR; the tasks + review will follow transitively.
       Architect lens: healthy inheritance shape — single design inherits,
       tasks + review cascade. No unrelated consumers.
       Reminder: this is wikilink-only. I'd grep `ADR-0007` across the
       repo (code + docs) before pulling the trigger."
```

**Forward 1 level from a spec-design:**
```
User: what does login-google-design depend on?
AI:   [analyze --seed login-google-design --direction forward --depth 1]
AI:   "Seed: login-google-design (spec-design). Forward, depth 1.
       Depends on: ADR-0007-oauth (adr), prd-auth (prd).
       Architect lens: dependencies point up the pyramid (design → ADR +
       PRD) — shape is correct."
```

**Markdown output for a human review:**
```
User: /sdlc-kit:impact ADR-0007-oauth --format markdown --depth 3
AI:   [analyze ... --format markdown]
AI:   <renders the returned `markdown` field as a tree + by-type section
       + edge table for the reviewer>
```

**Both directions (planning a big rename):**
```
User: /sdlc-kit:impact login-google-design --direction both --depth 2
AI:   "Seed: login-google-design. Union walk, depth 2.
       Backward (2): login-google-tasks, pr-0001-login-google.
       Forward  (2): ADR-0007-oauth, prd-auth.
       Total touched: 4. Engineer lens: if you rename this slug, 2
       downstream files need retarget and 2 upstream references need to
       be updated in this file. Reminder: wikilinks only — grep first."
```

**Ambiguous / missing seed:**
```
User: /sdlc-kit:impact login-google
AI:   [analyze --seed login-google]  → exit 1, "seed `login-google` not
       found (no stem, slug, or title match)".
AI:   "I didn't find a note with stem, slug, or title `login-google`.
       Did you mean `login-google-design` or `login-google-tasks`?"
```

---

## See also

- `scripts/impact.py` — read-only analyzer.
- `/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:spec`, `/sdlc-kit:prd` —
  the scaffold / transition skills to hand off to after an impact review.
- `/sdlc-kit:sync` — regenerate `_INDEX.md` and MOCs after any mutation
  triggered by an impact finding.
