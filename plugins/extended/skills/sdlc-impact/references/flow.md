# sdlc-kit:impact — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available (PEP 604 unions).
3. **Seed exists.** The script refuses missing/ambiguous seeds with exit code 1.

## Flow

### Invoke: `/sdlc-kit:impact <seed>`

1. **Pick the direction.** Default `backward` ("who depends on the seed?"). Use `forward` for "what does this depend on?" and `both` for union.
2. **Pick the depth.** Default 3. Use 1 for immediate neighbours, up to 10 for deep traces. Anything above 10 is silently clamped.
3. **Run the analyzer.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-impact/scripts/impact.py" \
     --vault-root "<vault>" --action analyze \
     --seed "<seed>" \
     [--direction backward|forward|both] \
     [--depth N] \
     [--format json|markdown]
   ```
4. **Present the result.** Engineer lens names the number of dependents and groups by type; architect lens comments on shape (healthy inheritance vs smell — single seed referenced by dozens of unrelated docs = split candidate).
5. **Always remind** the user the graph is wikilink-only — suggest grep / code search for destructive actions.

### Seed resolution

Accepts a stem, a frontmatter `slug`, or a frontmatter `title`, in that order
of precedence. If ambiguous, script exits with code 1 and lists candidates.

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

With `--format markdown`, the same object carries an extra `markdown` field
with a human-readable tree grouped by depth, by-type breakdown, and edge table.

**Exit codes:** `0` ok · `1` user error (seed not found, ambiguous, not a vault, empty vault) · `2` fatal.

## Guardrails

**Never:**
- Present the graph as the *full* impact picture. Wikilinks only — always remind the user.
- Follow frontmatter wikilinks as graph edges — only body is walked.
- Write to the vault. Read-only. Hand off to the relevant scaffold skill.
- Silently expand depth past 10 — the script clamps; say so in the report.
- Treat "no dependents reached" as proof of isolation — plain text and code may still reference.

**Always:**
- Match the user's active conversation language.
- State direction, depth, and seed at the top of every answer.
- Group dependents by `doc_type` in summary — most actionable slice.
- Offer next step: hand off to type-specific skill, or widen depth / flip direction.
- Cap the answer at actual data. If zero dependents at chosen depth, say so plainly.

## Examples

**Backward 2 levels from an ADR (before deprecation):**
```
User: /sdlc-kit:impact ADR-0007-oauth --depth 2
AI:   [analyze --seed ADR-0007-oauth --direction backward --depth 2]
AI:   "Seed: ADR-0007-oauth (adr). Backward, depth 2.
       3 dependents — 1 spec-design, 1 spec-tasks, 1 review.
       Engineer lens: before deprecating, retarget login-google-design to the
       successor ADR; tasks + review follow transitively.
       Architect lens: healthy inheritance shape.
       Reminder: wikilink-only. Grep `ADR-0007` before pulling the trigger."
```

**Forward 1 level from a spec-design:**
```
User: what does login-google-design depend on?
AI:   [analyze --direction forward --depth 1]
AI:   "Depends on: ADR-0007-oauth (adr), prd-auth (prd).
       Architect lens: dependencies point up the pyramid — shape is correct."
```

**Markdown output for a human review:**
```
User: /sdlc-kit:impact ADR-0007-oauth --format markdown --depth 3
AI:   [analyze ... --format markdown]
AI:   <renders the returned `markdown` field>
```

**Both directions (planning a big rename):**
```
User: /sdlc-kit:impact login-google-design --direction both --depth 2
AI:   "Union walk, depth 2.
       Backward (2): login-google-tasks, pr-0001-login-google.
       Forward  (2): ADR-0007-oauth, prd-auth.
       Engineer: 2 downstream retargets + 2 upstream references to update."
```

**Ambiguous / missing seed:**
```
User: /sdlc-kit:impact login-google
AI:   [exit 1] "seed `login-google` not found (no stem/slug/title match).
       Did you mean `login-google-design` or `login-google-tasks`?"
```

## See also

- `scripts/impact.py` — read-only analyzer.
- `/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:spec`, `/sdlc-kit:prd` — scaffold/transition skills to hand off to.
- `/sdlc-kit:sync` — regenerate `_INDEX.md` after mutations.
