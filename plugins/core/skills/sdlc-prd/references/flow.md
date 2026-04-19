# sdlc-kit:prd — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/01-planning/_templates/prd.md.tpl`.

## Flow

### Zero-arg / list: `/sdlc-kit:prd` or `/sdlc-kit:prd list`

1. Run `prd.py --action list`.
2. Show compact table: `slug | status | title | updated`.
3. Offer next action.

### New PRD: `/sdlc-kit:prd new <title>`

1. **Derive slug.** Propose from the title (lowercase ASCII, hyphen-separated). Allow override.
2. **Status check.** Run `--action list` first.
3. **Collision?** If `<slug>.md` exists, ask whether to open existing, pick a different slug, or overwrite (`--force`).
4. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-prd/scripts/prd.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<owner>"]
   ```
5. **Interview** (below).

### The interview (LLM-driven, section by section)

Walk the template sections, one focused question per section. Edit in place
via the Edit tool — never rewrite the whole file at once. Match user's chat
language; template headings stay in template language.

1. **Context** — current situation and what is changing (2–4 paragraphs).
2. **Problem** — concrete, measurable: who, how often, what impact.
3. **Hypotheses** — 1–3 testable hypotheses, each with metric/experiment that validates it.
4. **Scope** — in-scope vs out-of-scope. Out-of-scope matters as much.
5. **KPIs** — 1–3 metrics with baseline, target, deadline.
6. **Risks** — top 2–3 with probability, impact, mitigation.
7. **Schedule** — kickoff, milestones, GA. Placeholders OK if unresolved.
8. **Stakeholders** — sponsor, product owner, tech lead, design lead.

Keep ≤ 8 questions. If user has no answer, leave placeholder and revisit later.

### Transition: `/sdlc-kit:prd {promote|ship|archive|reopen} <slug>`

| Verb | Target status | When to use |
|---|---|---|
| `promote` | `active` | Draft reviewed, owner signed off |
| `ship` | `shipped` | Initiative reached GA / delivered KPIs |
| `archive` | `archived` | Cancelled, deprioritized, or superseded |
| `reopen` | `draft` | Needs more work; active was premature |

```bash
python "...prd.py" --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|active|shipped|archived>"
```

No-op if already at target status (idempotent).

### Sync

After every scaffold or transition, invoke `/sdlc-kit:sync`.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "prds": [
    {"slug": "auth-login", "path": "01-planning/prd/auth-login.md",
     "title": "Autenticação com Google", "status": "active",
     "owner": "Milton", "updated": "2026-04-17"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "checkout-v2",
  "prd_path": "01-planning/prd/checkout-v2.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "auth-login", "prd_path": "01-planning/prd/auth-login.md",
  "previous_status": "draft", "new_status": "active",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Overwrite without `--force` and explicit confirmation.
- Rewrite the entire PRD in one Edit call.
- Auto-promote to `active` — `active` means the product owner signed off.
- Fabricate KPIs, hypotheses, or stakeholder names.
- Silently rename a PRD. Archive the old one and scaffold new so wikilink history stays traceable.

**Always:**
- Match the user's active conversation language.
- Run `--action list` before scaffold.
- Invoke `/sdlc-kit:sync` after scaffold or transition.
- Surface the generated file path so the user can open it.
- When transitioning to `active` or `shipped`, remind which sections downstream artefacts (epics, specs, ADRs) link back to.

## Examples

**New initiative from scratch:**
```
User: /sdlc-kit:prd new Checkout v2
AI:   Proposed slug: `checkout-v2`. OK?
User: ok
AI:   [list] no collision. [scaffold]
AI:   "Let's fill this in. **Context** — describe the current situation in 2-4 paragraphs."
User: <answer>
AI:   [Edit: replace Context]
…
AI:   "All 8 sections filled. Promote to `status: active`? (y/n)"
User: not yet — review with PO first
AI:   "Leaving as `draft`. When ready: `/sdlc-kit:prd promote checkout-v2`."
```

**Promoting a mature draft:**
```
User: /sdlc-kit:prd promote checkout-v2
AI:   [list] checkout-v2 (draft).
AI:   "Confirm promoting checkout-v2 draft→active? PO signed off?"
User: yes, PO approved yesterday
AI:   [transition][/sdlc-kit:sync]
AI:   "✓ active. Suggested next step: `/sdlc-kit:epic new …`."
```

**Idempotent:**
```
User: /sdlc-kit:prd promote auth-login
AI:   [list] auth-login already active — nothing to do.
```

## See also

- `scripts/prd.py` — file-op helper.
- `assets/vault-tree/01-planning/_templates/prd.md.tpl`.
- `/sdlc-kit:steer product`, `/sdlc-kit:epic`, `/sdlc-kit:spec`, `/sdlc-kit:sync`.
